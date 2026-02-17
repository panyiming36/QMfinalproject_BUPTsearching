import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS, FOAF
import urllib.parse
import re
import hashlib
from datetime import datetime
import os

class BUPTResearchRDF:
    def __init__(self):
        self.g = Graph()
        self.setup_namespaces()
        self.paper_count = 0
        self.triple_count = 0
        
    def setup_namespaces(self):
        self.BUPT = Namespace("http://bupt.edu.cn/research/")
        self.BUPT_ONTOLOGY = Namespace("http://bupt.edu.cn/ontology/")
        self.SCHEMA = Namespace("http://schema.org/")
        
        self.g.bind("bupt", self.BUPT)
        self.g.bind("bupt-onto", self.BUPT_ONTOLOGY)
        self.g.bind("schema", self.SCHEMA)
        self.g.bind("dcterms", DCTERMS)
        self.g.bind("foaf", FOAF)
        self.g.bind("rdfs", RDFS)
        self.g.bind("xsd", XSD)
    
    def create_uri_safe(self, text):
        if pd.isna(text):
            return "unknown"
        return urllib.parse.quote(str(text).strip().replace(' ', '_'), safe='')
    
    def extract_year(self, pub_time):
        if pd.isna(pub_time):
            return None
        pub_str = str(pub_time)
        match = re.search(r'\b(20\d{2}|19\d{2})\b', pub_str)
        return match.group(1) if match else None
    
    def process_paper(self, idx, row):
        paper_id = f"paper_{idx+1:04d}"
        paper_uri = self.BUPT[paper_id]
        
        
        if (idx + 1) % 50 == 0:
            print(f"正在处理第 {idx + 1} 篇论文...")
        
        
        self.g.add((paper_uri, RDF.type, self.SCHEMA.ScholarlyArticle))
        self.triple_count += 1
        
        
        if 'SrcDatabase-来源库' in row and pd.notna(row['SrcDatabase-来源库']):
            src_type = str(row['SrcDatabase-来源库']).strip()
            self.g.add((paper_uri, DCTERMS.type, Literal(src_type, lang='zh')))
            self.g.add((paper_uri, self.BUPT_ONTOLOGY.sourceDatabase, Literal(src_type, lang='zh')))
            self.triple_count += 2
        
        
        if 'Title-题名' in row and pd.notna(row['Title-题名']):
            title = str(row['Title-题名']).strip()
            self.g.add((paper_uri, DCTERMS.title, Literal(title, lang='zh')))
            self.g.add((paper_uri, self.SCHEMA.name, Literal(title, lang='zh')))
            self.triple_count += 2
        
        
        if 'Author-作者' in row and pd.notna(row['Author-作者']):
            authors = str(row['Author-作者']).split(';')
            
            
            org_text = ""
            if 'Organ-单位' in row and pd.notna(row['Organ-单位']):
                org_text = str(row['Organ-单位'])
            
            org_list = org_text.split(';') if org_text else []
            
            for i, author_name in enumerate(authors):
                author_name = author_name.strip()
                if author_name:
                    author_id = hashlib.md5(author_name.encode('utf-8')).hexdigest()[:8]
                    author_uri = self.BUPT[f"author/{author_id}"]
                    
                    
                    self.g.add((author_uri, RDF.type, FOAF.Person))
                    self.g.add((author_uri, FOAF.name, Literal(author_name, lang='zh')))
                    self.g.add((author_uri, self.SCHEMA.name, Literal(author_name, lang='zh')))
                    
                    
                    self.g.add((paper_uri, DCTERMS.creator, author_uri))
                    self.g.add((paper_uri, self.SCHEMA.author, author_uri))
                    
                    
                    if i < len(org_list) and org_list[i].strip():
                        org_name = org_list[i].strip()
                        org_id = hashlib.md5(org_name.encode('utf-8')).hexdigest()[:8]
                        org_uri = self.BUPT[f"org/{org_id}"]
                        
                        
                        self.g.add((org_uri, RDF.type, self.SCHEMA.Organization))
                        self.g.add((org_uri, self.SCHEMA.name, Literal(org_name, lang='zh')))
                        
                        
                        self.g.add((author_uri, self.SCHEMA.affiliation, org_uri))
                        self.g.add((org_uri, self.SCHEMA.member, author_uri))
                        self.triple_count += 5
                    
                    self.triple_count += 5
        
        
        if 'Source-文献来源' in row and pd.notna(row['Source-文献来源']):
            source = str(row['Source-文献来源']).strip()
            journal_id = hashlib.md5(source.encode('utf-8')).hexdigest()[:8]
            journal_uri = self.BUPT[f"journal/{journal_id}"]
            
            
            self.g.add((journal_uri, RDF.type, self.SCHEMA.Periodical))
            self.g.add((journal_uri, RDF.type, self.SCHEMA.PublicationVolume))
            self.g.add((journal_uri, self.SCHEMA.name, Literal(source, lang='zh')))
            self.g.add((journal_uri, DCTERMS.title, Literal(source, lang='zh')))
            
           
            self.g.add((paper_uri, DCTERMS.source, journal_uri))
            self.g.add((paper_uri, self.SCHEMA.isPartOf, journal_uri))
            self.g.add((journal_uri, self.SCHEMA.hasPart, paper_uri))
            self.triple_count += 8
        
        
        if 'Keyword-关键词' in row and pd.notna(row['Keyword-关键词']):
            keywords = str(row['Keyword-关键词']).split(';')
            for keyword in keywords:
                keyword = keyword.strip()
                if keyword:
                    keyword_id = hashlib.md5(keyword.encode('utf-8')).hexdigest()[:8]
                    keyword_uri = self.BUPT[f"keyword/{keyword_id}"]
                    
                    
                    self.g.add((keyword_uri, RDF.type, self.SCHEMA.DefinedTerm))
                    self.g.add((keyword_uri, self.SCHEMA.name, Literal(keyword, lang='zh')))
                    self.g.add((keyword_uri, self.SCHEMA.termCode, Literal(keyword, lang='zh')))
                    
                    
                    self.g.add((paper_uri, self.SCHEMA.keywords, keyword_uri))
                    self.g.add((paper_uri, self.SCHEMA.about, keyword_uri))
                    self.g.add((keyword_uri, self.SCHEMA.isRelatedTo, paper_uri))
                    self.triple_count += 6
        
        
        if 'Summary-摘要' in row and pd.notna(row['Summary-摘要']):
            summary = str(row['Summary-摘要']).strip()
            if len(summary) > 1000:
                summary = summary[:1000] + "..."
            self.g.add((paper_uri, DCTERMS.abstract, Literal(summary, lang='zh')))
            self.g.add((paper_uri, self.SCHEMA.description, Literal(summary, lang='zh')))
            self.triple_count += 2
        
        
        if 'PubTime-发表时间' in row and pd.notna(row['PubTime-发表时间']):
            pub_time = str(row['PubTime-发表时间'])
            year = self.extract_year(pub_time)
            if year:
                self.g.add((paper_uri, DCTERMS.date, Literal(year, datatype=XSD.gYear)))
                self.g.add((paper_uri, self.SCHEMA.datePublished, Literal(year, datatype=XSD.gYear)))
                self.triple_count += 2
        
        
        if 'URL-网址' in row and pd.notna(row['URL-网址']):
            url = str(row['URL-网址']).strip()
            if url.startswith('http'):
                self.g.add((paper_uri, self.SCHEMA.url, Literal(url, datatype=XSD.anyURI)))
                self.triple_count += 1
        
        self.paper_count += 1
        return paper_uri
    
    def convert(self, file_path, output_dir="output"):
        print("开始RDF转换...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"读取文件: {file_path}")
        
        try:
            
            df = pd.read_excel(file_path, engine='xlrd')
            print(f"成功读取Excel文件，共 {len(df)} 行")
            
        except Exception as e:
            print(f"读取Excel失败: {e}")
            
            try:
                df = pd.read_excel(file_path)
                print(f"使用默认引擎成功读取，共 {len(df)} 行")
            except Exception as e2:
                print(f"所有引擎都失败: {e2}")
                return None
        
        print(f"发现记录: {len(df)} 条")
        
        
        print("\n前几行数据:")
        print(df.head())
        print("\n列名:", df.columns.tolist())
        
        
        initial_count = len(df)
        df = df.dropna(subset=['Title-题名'])
        print(f"\n移除空标题行后: {len(df)}/{initial_count} 条有效记录")
        
        
        column_mapping = {}
        for col in df.columns:
            col_str = str(col)
            
            if any(term in col_str for term in ['SrcDatabase', '来源库']):
                column_mapping[col] = 'SrcDatabase-来源库'
            elif any(term in col_str for term in ['Title', '题名']):
                column_mapping[col] = 'Title-题名'
            elif any(term in col_str for term in ['Author', '作者']):
                column_mapping[col] = 'Author-作者'
            elif any(term in col_str for term in ['Organ', '单位']):
                column_mapping[col] = 'Organ-单位'
            elif any(term in col_str for term in ['Source', '文献来源']):
                column_mapping[col] = 'Source-文献来源'
            elif any(term in col_str for term in ['Keyword', '关键词']):
                column_mapping[col] = 'Keyword-关键词'
            elif any(term in col_str for term in ['Summary', '摘要']):
                column_mapping[col] = 'Summary-摘要'
            elif any(term in col_str for term in ['PubTime', '发表时间']):
                column_mapping[col] = 'PubTime-发表时间'
            elif any(term in col_str for term in ['URL', '网址']):
                column_mapping[col] = 'URL-网址'
        
        if column_mapping:
            print("\n重命名列:")
            for old, new in column_mapping.items():
                print(f"  {old} -> {new}")
            df = df.rename(columns=column_mapping)
        
        print("\n转换为RDF三元组...")
        for idx, row in df.iterrows():
            self.process_paper(idx, row)
            
            if (idx + 1) % 50 == 0:
                print(f"已处理 {idx + 1}/{len(df)} 条记录")
        
        
        complete_ttl = f"{output_dir}/complete_bupt_research.ttl"
        self.g.serialize(destination=complete_ttl, format='turtle')
        print(f"\n✓ 完整RDF已保存: {complete_ttl}")
        
        
        self.generate_report(output_dir)
        
        return self.g
    
    def generate_report(self, output_dir):
        report_path = f"{output_dir}/conversion_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RDF转换报告\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"论文数量: {self.paper_count}\n")
            f.write(f"三元组总数: {self.triple_count}\n")
            f.write(f"平均每篇论文三元组数: {self.triple_count/self.paper_count:.1f}\n")
            
            
            f.write("\n关系类型统计:\n")
            
            
            predicates = {}
            for s, p, o in self.g:
                pred_str = str(p)
                if pred_str not in predicates:
                    predicates[pred_str] = 0
                predicates[pred_str] += 1
            
            
            sorted_preds = sorted(predicates.items(), key=lambda x: x[1], reverse=True)
            
            for pred, count in sorted_preds:
                
                if 'schema.org' in pred:
                    pred = pred.replace('http://schema.org/', 'schema:')
                elif 'purl.org/dc/terms/' in pred:
                    pred = pred.replace('http://purl.org/dc/terms/', 'dcterms:')
                elif 'xmlns.com/foaf/0.1/' in pred:
                    pred = pred.replace('http://xmlns.com/foaf/0.1/', 'foaf:')
                f.write(f"{pred}: {count} 次\n")
            
            f.write("\n创建的所有关系类型:\n")
            f.write("1. 类型关系: bupt:paper_XXXX a schema:ScholarlyArticle\n")
            f.write("2. 标题关系: bupt:paper_XXXX schema:name '标题'@zh\n")
            f.write("3. 作者关系: bupt:paper_XXXX schema:author bupt:author/XXXX\n")
            f.write("4. 机构关系: bupt:author/XXXX schema:affiliation bupt:org/XXXX\n")
            f.write("5. 期刊关系: bupt:paper_XXXX schema:isPartOf bupt:journal/XXXX\n")
            f.write("6. 关键词关系: bupt:paper_XXXX schema:keywords bupt:keyword/XXXX\n")
            f.write("7. 时间关系: bupt:paper_XXXX schema:datePublished '2023'^^xsd:gYear\n")
            f.write("8. URL关系: bupt:paper_XXXX schema:url 'http://...'^^xsd:anyURI\n")
            
            
            f.write("\n第一篇论文示例:\n")
            paper_uri = self.BUPT["paper_0001"]
            for s, p, o in self.g.triples((paper_uri, None, None)):
                
                p_str = str(p)
                o_str = str(o)
                if 'schema.org' in p_str:
                    p_str = p_str.replace('http://schema.org/', 'schema:')
                if 'schema.org' in o_str and '/' in o_str:
                    o_str = o_str.replace('http://schema.org/', 'schema:')
                f.write(f"  {p_str} -> {o_str[:50]}...\n")
        
        print(f"\n报告已生成: {report_path}")

def create_unified_store(rdf_graph, store_dir="unified_store"):
    print("\n创建统一的三元组存储...")
    
    os.makedirs(store_dir, exist_ok=True)
    
    
    complete_store = f"{store_dir}/complete_store.ttl"
    rdf_graph.serialize(destination=complete_store, format='turtle')
    print(f"✓ 完整统一存储: {complete_store}")
    
    
    triples = len(list(rdf_graph))
    print(f"✓ 总三元组数: {triples}")
    
    return store_dir

def main():
    print("=" * 60)
    print("BUPT研究数据RDF转换 - 统一存储")
    print("=" * 60)
    
    file_path = "bupt.xls"
    if not os.path.exists(file_path):
        print(f"错误：文件 '{file_path}' 不存在！")
        print("请确保文件在当前目录下")
        return
    
    print(f"处理文件: {file_path}")
    
    
    converter = BUPTResearchRDF()
    rdf_graph = converter.convert(file_path, output_dir="output")
    
    if rdf_graph:
        
        store_dir = create_unified_store(rdf_graph, store_dir="unified_store")
        
        print("\n" + "=" * 60)
        print("转换完成！")
        print("=" * 60)
        print("\n生成的文件:")
        print(f"  output/complete_bupt_research.ttl - 完整RDF文件")
        print(f"  output/conversion_report.txt - 转换报告")
        print(f"  {store_dir}/complete_store.ttl - 统一存储")
        
        print(f"\n关键统计:")
        print(f"  处理论文数: {converter.paper_count}")
        print(f"  生成三元组数: {converter.triple_count}")
        print(f"  平均每篇论文三元组数: {converter.triple_count/converter.paper_count:.1f}")
        
        print(f"\nRDF包含的所有关系类型:")
        print("  1. 类型关系 (论文 → 学术文章)")
        print("  2. 标题关系 (论文 → 标题)")
        print("  3. 作者关系 (论文 → 作者)")
        print("  4. 机构关系 (作者 → 单位)")
        print("  5. 期刊关系 (论文 → 期刊)")
        print("  6. 关键词关系 (论文 → 关键词)")
        print("  7. 时间关系 (论文 → 发表年份)")
        print("  8. URL关系 (论文 → 链接)")
        
        print(f"\n查看 'output/conversion_report.txt' 获取详细关系示例")
        print("=" * 60)
    else:
        print("转换失败！")

if __name__ == "__main__":
    main()