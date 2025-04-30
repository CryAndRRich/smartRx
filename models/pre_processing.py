import os
import glob
import pickle
import copy
import argparse
import itertools
import pandas as pd
import time
from rdkit import DataStructs
from rdkit.Chem import AllChem
from rdkit import Chem
from tqdm import tqdm

def parse_food_input(input_file: str): 
    """
    Nhận vào 1 file chứa danh sách loại thuốc - thực phẩm theo cặp:
    +) Trích xuất tên và mã hợp chất từng loại thuốc - thực phẩm
    +) Tra cứu thông tin SMILES của thuốc và CAS number của thực phẩm từ 2 file csv trong dataset
    +) Trả kết quả là 1 file parsed_input.txt"""
    parsed=open('Data/Dataset/parsed_input.txt','w+')
    parsed.write('Prescription	Drug name	Smiles\n')
    food_compound = pd.read_csv('Data/Dataset/food_compounds_lookup.csv')
    merged=pd.read_csv('Data/Dataset/drug_info_combined.csv')
    all_d=[]
    all_f=[]

    first_line=True
    with open(input_file, 'r') as fp:
        for line in fp:
            each_input=[i.lower() for i in line.strip().split('\t')]
            if first_line:
                for i in each_input:
                    all_d.append(i)
                first_line=False                      
            else:
                for i in each_input:
                    all_f.append(i)
    
    assert len(all_d)>=1 and len(all_f)>=1, 'No valid pairs entered'
    count=0
    for i in all_d:
        drug_name,drug_com=i.strip().lower().split('|')
        name_i = drug_name+'('+drug_com+')'+'\t'
        find_drug_1=merged.loc[merged['Name'].str.lower()==drug_com.lower()]
        smile_i=find_drug_1['Smiles'].values[0]+'\n'

        for j in all_f:
            food_name,food_comp=j.strip().lower().split('|')
            
            each_i=str(count)+'\t'
            each_j=str(count)+'\t'
        # Tìm kiếm thực phẩm trong danh sách
            
            each_i += name_i
            each_j += food_name+'('+food_comp+')'+'\t'
            
            find_food_2 = food_compound.loc[food_compound['name'].str.lower()==food_comp.lower()]
            smile_j = find_food_2['cas_number'].values[0]+'\n'
            
            each_i+=smile_i
            each_j+=smile_j
            parsed.write(each_i)
            parsed.write(each_j)
            count+=1
    parsed.close()
    return

def parse_drug_input(input_file: str):
    """
    Đầu vào là file chứa danh sách thuốc:
    +) Tách ra thuốc chính (current_drugs) và thuốc khác (other_drugs)
    +) Truy xuất thông tin SMILES cho từng loại thuốc trong file Drug_info_combined.csv
    +) Ghi dữ liệu ra file parsed_input.txt"""
    parsed=open('Data/Dataset/parsed_input.txt','w+')
    parsed.write('Prescription	Drug name	Smiles\n')
    merged=pd.read_csv('Data/Dataset/Drug_info_combined.csv')
    approved_drugs=set(merged['Name'].str.lower())
    current_drug=[]
    other_drugs=[]

    first_line=True
    with open(input_file, 'r') as fp:
        for line in fp:
            if first_line:
                current_drug=line.strip().split('\t')
                first_line=False
            else:
                other_drugs=line.strip().split('\t')

    count=0
    for i in current_drug:
        drug_name_i,drug_com_i=i.strip().lower().split('|')
        name_i = drug_name_i+'('+drug_com_i+')'+'\t'
        find_drug_1=merged.loc[merged['Name'].str.lower()==drug_com_i]

        for j in other_drugs:
            drug_name_j,drug_com_j=j.strip().lower().split('|')

            each_i=str(count)+'\t'
            each_j=str(count)+'\t'
        # Tìm kiếm thuốc trong danh sách
            find_drug_2=merged.loc[merged['Name'].str.lower()==drug_com_j]

            name_j = drug_name_j+'('+drug_com_j+')'+'\t'

            each_i += name_i
            each_j += name_j
            
            smile_i=find_drug_1['Smiles'].values[0]+'\n'
            smile_j=find_drug_2['Smiles'].values[0]+'\n'
            
            each_i+=smile_i
            each_j+=smile_j
            parsed.write(each_i)
            parsed.write(each_j)
            count+=1
    parsed.close()
    return 


def parse_DDI_input_file(input_file: str, output_file: str):
    """
    Đọc file chứa thông tin thuốc theo đơn, và sinh ra tất cả các cặp thuốc (pairs) 
    trong mỗi đơn, kèm theo SMILES của từng thuốc
    """
    drug_pair_info = {}
    drug_smiles_info = {}
    with open(input_file, 'r') as fp:
        for line in fp:
            sptlist = line.strip().split('\t')
            prescription = sptlist[0].strip()
            drug_name = sptlist[1].strip()
            smiles = sptlist[2].strip()
            
            drug_smiles_info[(prescription, drug_name)] = smiles
            if prescription not in drug_pair_info:
                drug_pair_info[prescription] = [drug_name]
            else:
                drug_pair_info[prescription].append(drug_name)
            
        
    out_fp = open(output_file, 'w')
    for each_prescription in drug_pair_info:
        drug_names = drug_pair_info[each_prescription]
        for each_set in itertools.combinations(drug_names, 2):
            drug1 = each_set[0].strip()
            drug1_smiles = drug_smiles_info[(each_prescription, drug1)] 
            drug2 = each_set[1].strip()
            drug2_smiles = drug_smiles_info[(each_prescription, drug2)] 
            out_fp.write('%s\t%s\t%s\t%s\t%s\n'%(each_prescription, drug1, drug1_smiles, drug2, drug2_smiles))
    out_fp.close()
    return

# Các hàm calculate
def calculate_drug_similarity(drug_dir: str, input_dir: str, output_file):
    """
    Tính độ tương đồng cấu trúc (structural similarity) giữa các thuốc từ 
    thư viện DrugBank với các thuốc đầu vào trả về 1 file csv lưu ma trận tương đồng
    """
    drugbank_files = glob.glob(os.path.join(drug_dir, '*.mol'))
    input_files = glob.glob(os.path.join(input_dir, '*.mol'))

    drug_similarity_info = {}

    for drugbank_path in tqdm(drugbank_files, desc="DrugBank"):
        drugbank_id = os.path.splitext(os.path.basename(drugbank_path))[0]
        drug1_mol = Chem.MolFromMolFile(drugbank_path)
        if drug1_mol is None:
            continue
        drug1_mol = AllChem.AddHs(drug1_mol)
        drug1_fp = AllChem.GetMorganFingerprint(drug1_mol, 2)
        drug_similarity_info[drugbank_id] = {}

        for input_path in input_files:
            input_id = os.path.splitext(os.path.basename(input_path))[0]
            drug2_mol = Chem.MolFromMolFile(input_path)
            if drug2_mol is None:
                continue
            drug2_mol = AllChem.AddHs(drug2_mol)
            drug2_fp = AllChem.GetMorganFingerprint(drug2_mol, 2)
            score = DataStructs.TanimotoSimilarity(drug1_fp, drug2_fp)
            drug_similarity_info[drugbank_id][input_id] = score

    pd.DataFrame.from_dict(drug_similarity_info).to_csv(output_file)

def calculate_structure_similarity(drug_dir: str, input_file: str, output_file: str, drug_list):
    """
    So sánh độ tương đồng giữa các thuốc đầu vào (dạng SMILES) 
    và các thuốc trong DrugBank (dạng file .mol)
    """
    drugbank_files = glob.glob(os.path.join(drug_dir, '*.mol'))

    all_input_drug_info = {}
    with open(input_file, 'r') as fp:
        for line in fp:
            spt = line.strip().split('\t')
            if len(spt) < 5:
                continue
            _, drug1, smiles1, drug2, smiles2 = spt
            all_input_drug_info.setdefault(drug1, smiles1)
            all_input_drug_info.setdefault(drug2, smiles2)

    drug_similarity_info = {}

    for input_id, smiles in tqdm(all_input_drug_info.items(), desc="Input drugs"):
        try:
            drug2_mol = Chem.MolFromSmiles(smiles)
            if drug2_mol is None:
                continue
            drug2_mol = AllChem.AddHs(drug2_mol)
            drug2_fp = AllChem.GetMorganFingerprint(drug2_mol, 2)
        except:
            continue

        drug_similarity_info[input_id] = {}
        for drugbank_path in drugbank_files:
            drugbank_id = os.path.splitext(os.path.basename(drugbank_path))[0]
            drug1_mol = Chem.MolFromMolFile(drugbank_path)
            if drug1_mol is None:
                continue
            drug1_mol = AllChem.AddHs(drug1_mol)
            drug1_fp = AllChem.GetMorganFingerprint(drug1_mol, 2)
            score = DataStructs.TanimotoSimilarity(drug1_fp, drug2_fp)
            drug_similarity_info[input_id][drugbank_id] = score

    df = pd.DataFrame.from_dict(drug_similarity_info).T
    df = df[drug_list] if drug_list else df
    df.to_csv(output_file)


def calculate_pca(similarity_profile_file, output_file, pca_model):
    """
    Giảm chiều dữ liệu đặc trưng của 1 loại thuốc bằng PCA (Principal Component Analysis)
    """
    with open(pca_model, 'rb') as fid:
        pca = pickle.load(fid)

    df = pd.read_csv(similarity_profile_file, index_col=0)
    X = df.values
    X_pca = pca.transform(X)

    pca_df = pd.DataFrame(X_pca,
                          index=df.index,
                          columns=[f'PC_{i+1}' for i in range(X_pca.shape[1])])
    pca_df.to_csv(output_file)



def generate_input_profile(input_file, pca_profile_file):  
    """
    +) Đọc file chứa các cặp thuốc từ đơn thuốc (input_file)
    +) Đọc file vector PCA của từng thuốc (pca_profile_file)
    +) Với mỗi cặp thuốc (drug1, drug2), kết hợp vector PCA của cả 2 thành 1 vector 100 chiều (50+50)
    +) Trả về một Dataframe để đưa vào model 
    """  
    df = pd.read_csv(pca_profile_file, index_col=0)
    # df.index = df.index.map(str)
    
    all_drugs = []
    interaction_list = []
    with open(input_file, 'r') as fp:
        for line in fp:
            sptlist = line.strip().split('\t')
            prescription = sptlist[0].strip()
            drug1 = sptlist[1].strip()
            drug2 = sptlist[3].strip()
            all_drugs.append(drug1)
            all_drugs.append(drug2)
            if drug1 in df.index and drug2 in df.index:
                interaction_list.append([prescription, drug1, drug2]) # Cặp A - B và Cặp B - A là tương tự 
                interaction_list.append([prescription, drug2, drug1]) 
    
    drug_feature_info = {}
    columns = ['PC_%d' % (i + 1) for i in range(50)]
    for row in df.itertuples():
        drug = row.Index
        feature = []
        drug_feature_info[drug] = {}
        for col in columns:
            val = getattr(row, col)
            feature.append(val)
            drug_feature_info[drug][col] = val

    new_col1 = ['1_%s'%(i) for i in columns]
    new_col2 = ['2_%s'%(i) for i in columns]
    
    DDI_input = {}
    for each_drug_pair in tqdm.tqdm(interaction_list):
        prescription = each_drug_pair[0]
        drug1 = each_drug_pair[1]
        drug2 = each_drug_pair[2]
        key = '%s_%s_%s' % (prescription, drug1, drug2)
        
        DDI_input[key] = {}
        for col in columns:
            new_col = '1_%s'%(col)
            DDI_input[key][new_col] = drug_feature_info[drug1][col]
            
        for col in columns:
            new_col = '2_%s'%(col)
            DDI_input[key][new_col] = drug_feature_info[drug2][col]

    new_columns = []
    for i in [1,2]:
        for j in range(1, 51):
            new_key = '%s_PC_%s'%(i, j)
            new_columns.append(new_key)
            
    df = pd.DataFrame.from_dict(DDI_input)
    df = df.T
    df = df[new_columns]
    # df.to_csv(output_file)
    return df

