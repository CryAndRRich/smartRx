from models import *

COMBINED_DRUG_PATH = "data/Dataset/Input_txt/combined_drug_lists.txt"
PARSED_INPUT_PATH = "data/Result/parsed_drug_input.csv"
OUTPUT_DDI_PATH = "data/Result/output_ddi.csv"
DRUG_DIR = "data/Dataset/DrugBank5.0_Approved_drugs"
OUTPUT_SIMILARITY_PATH = "data/Result/structure_similarity.csv"
DRUG_LIST_PATH = "data/Dataset/DrugList.txt"
OUTPUT_PCA_PATH = "data/Result/output_pca.csv"
PCA_MODEL_PATH = "data/Models/pca_model.pkl"
OUTPUT_PREDICT_DDI_PATH = "data/Result/output_ddi_predict.csv"
OUTPUT_PREDICT_SEVERITY_PATH = "data/Result/output_severity_predict.csv"
INTERACTION_INFO_PATH = "data/Dataset/Interaction_information.csv"
INTERACTION_INFO_MODEL_PATH = "data/Dataset/Interaction_information_model.csv"
OUTPUT_PREDICT_DDI_COMBINED_PATH = "data/Result/output_ddi_predict_combined.csv"
DRUG_SIMILARITY_PATH = "data/Dataset/drug_similarity.csv"
DRUG_BANK_KNOWN_DDI_PATH = "data/Dataset/DrugBank_known_ddi.txt"
DRUG_SIDE_EFFECT_PATH = "data/Dataset/Drug_Side_Effect.txt"
ANNOTATED_RESULT_PATH = "data/Result/annotated_result.csv"
ANNOTATED_SEVERITY_RESULT_PATH = "data/Result/annotated_severity_result.csv"
FINAL_OUTPUT_PATH = "data/Result/final_result.csv"
FILTER_FINAL_RESULT_PATH = "data/Result/filter_result.csv"
BINARIZER_MODEL_PATH = "data/Models/label_binarizer.pkl"
THRESHOLD_MODEL = 0.27
THRESHOLD_STRUCTURE = 0.7

# PREPROCESSING
parse_drug_input(input_file=COMBINED_DRUG_PATH)

parse_DDI_input_file(input_file=PARSED_INPUT_PATH,
                     output_file=OUTPUT_DDI_PATH)

calculate_structure_similarity(drug_dir=DRUG_DIR,
                               input_file=OUTPUT_DDI_PATH,
                               output_file=OUTPUT_SIMILARITY_PATH,
                               drug_list_file=DRUG_LIST_PATH)

calculate_pca(similarity_profile_file=OUTPUT_SIMILARITY_PATH,
              output_file=OUTPUT_PCA_PATH,
              pca_model_path=PCA_MODEL_PATH)

pca_df = generate_input_profile(input_file=OUTPUT_DDI_PATH,
                                pca_profile_file=OUTPUT_PCA_PATH)

# PREDICTION
predict_DDI(output_file=OUTPUT_PREDICT_DDI_PATH,
            pca_df=pca_df,
            binarizer_file=BINARIZER_MODEL_PATH,
            threshold=THRESHOLD_MODEL)


DDI_result_supplement(input_file=OUTPUT_PREDICT_DDI_PATH,
                      interaction_info_file=INTERACTION_INFO_PATH,
                      output_file=OUTPUT_PREDICT_DDI_COMBINED_PATH)

annotate_DDI_results(DDI_output_file=OUTPUT_PREDICT_DDI_COMBINED_PATH,
                     similarity_file=DRUG_SIMILARITY_PATH,
                     known_DDI_file=DRUG_BANK_KNOWN_DDI_PATH,
                     output_file=ANNOTATED_RESULT_PATH,
                     side_effect_information_file=DRUG_SIDE_EFFECT_PATH,
                     model_threshold=THRESHOLD_MODEL,
                     structure_threshold=THRESHOLD_STRUCTURE)

summarize_prediction_outcome(result_file=ANNOTATED_RESULT_PATH,
                             output_file=FINAL_OUTPUT_PATH,
                             information_file=INTERACTION_INFO_MODEL_PATH)

annotated_with_severity_result(input_file=ANNOTATED_RESULT_PATH,
                               output_file=ANNOTATED_SEVERITY_RESULT_PATH)

