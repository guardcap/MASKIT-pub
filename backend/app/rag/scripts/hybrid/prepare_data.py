import pandas as pd
import os
import time
from datetime import datetime

# 데이터 경로를 프로젝트 루트 기준으로 설정
SEED_DIR = os.path.join('.', 'data', 'seed')
STAGING_DIR = os.path.join('.', 'data', 'staging')

def debug_dataframe(df, field_name):
    """DataFrame 디버깅을 위한 헬퍼 함수"""
    print(f"\n=== {field_name} 디버그 정보 ===")
    print("컬럼:", df.columns.tolist())
    print("\n첫 5개 행:")
    print(df.head())
    if field_name in df.columns:
        print(f"\n{field_name} 필드의 유니크 값:", df[field_name].unique())
    print("=" * 40)

def preprocess_laws(df):
    """법령 데이터(C_laws.csv)를 전처리합니다."""
    try:
        # 데이터 디버깅
        debug_dataframe(df, 'effective_date')
        
        # 날짜 필드가 있으면 epoch time으로 변환
        if 'effective_date' in df.columns and 'revised_at' in df.columns:
            def convert_date(x):
                try:
                    if pd.isna(x) or not isinstance(x, str) or x in ['effective_date', 'revised_at']:
                        return 0
                    
                    # 날짜 문자열 전처리
                    x = str(x).strip()
                    if x.endswith('.'):
                        x = x.rstrip('.')
                    
                    # 하이픈(-) 포함된 경우
                    if '-' in x:
                        parts = x.split('-')
                        if len(parts) == 3:
                            year, month, day = parts
                            # 2자리 연도를 4자리로 변환
                            if len(year) == 2:
                                year = '20' + year
                            x = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    
                    try:
                        return int(time.mktime(datetime.strptime(x, '%Y-%m-%d').timetuple()))
                    except ValueError as e:
                        if x not in ['effective_date', 'revised_at']:  # 헤더는 무시
                            print(f"날짜 변환 실패 ({x}): {str(e)}")
                        return 0
                        
                except Exception as e:
                    if x not in ['effective_date', 'revised_at']:  # 헤더는 무시
                        print(f"날짜 처리 중 오류 ({x}): {str(e)}")
                    return 0
            
            # DataFrame의 실제 데이터 예시 출력
            real_data_example = df['effective_date'].iloc[1] if len(df) > 1 else 'No data'
            print(f"날짜 형식 변환 중... (effective_date 예시: {real_data_example})")
            
            # effective_date와 revised_at 중 더 최근 날짜 사용
            df['effective_timestamp'] = df['effective_date'].apply(convert_date)
            df['revised_timestamp'] = df['revised_at'].apply(convert_date)
            df['recency'] = df[['effective_timestamp', 'revised_timestamp']].max(axis=1)
            
            # 임시 열 삭제
            df = df.drop(['effective_timestamp', 'revised_timestamp'], axis=1)
            
        # 추가 메타데이터 필드 생성
        df['CRITICAL_score'] = {'type': 'dict', 'value': {'CRITICAL_지수': 0.6}}  # 기본값 설정
        df['OPEN_score'] = {'type': 'dict', 'value': {'OPEN_지수': 0.4}}  # 기본값 설정
        
        return df
    except Exception as e:
        print(f"법령 데이터 전처리 중 오류: {e}")
        return df

def preprocess_gdpr(df):
    """GDPR 데이터를 전처리합니다."""
    try:
        # 데이터 디버깅
        debug_dataframe(df, 'Article Number')
        
        # GDPR 데이터를 C_laws.csv 형식에 맞게 변환
        df['law_id'] = 'GDPR'
        df['law_name'] = 'GDPR - General Data Protection Regulation'
        df['article_num'] = df['Article Number']
        df['article_title'] = df['Article Name']
        df['content'] = df['Content']
        df['law_category'] = 'EU'
        df['chapter_name'] = df['Chapter Name']
        df['article_type'] = 'GDPR'
        
        # 메타데이터 필드 생성
        df['CRITICAL_score'] = {'type': 'dict', 'value': {'CRITICAL_지수': 0.7}}  # GDPR은 중요도가 높으므로 0.7로 설정
        df['OPEN_score'] = {'type': 'dict', 'value': {'OPEN_지수': 0.3}}
        
        return df[['law_id', 'law_name', 'article_num', 'article_title', 'content', 
                  'law_category', 'chapter_name', 'article_type', 'CRITICAL_score', 'OPEN_score']]
    except Exception as e:
        print(f"GDPR 데이터 전처리 중 오류: {e}")
        return df

def main():
    """메인 전처리 함수"""
    print("데이터 전처리를 시작합니다...")
    
    # 출력 디렉터리가 없으면 생성
    os.makedirs(STAGING_DIR, exist_ok=True)
    
    # 1. A_cases.csv 처리
    print("A_cases.csv 파일을 처리 중입니다...")
    try:
        df_a = pd.read_csv(os.path.join(SEED_DIR, 'A_cases.csv'), dtype=str)
        # A_cases 전처리: before_text와 after_text를 결합하여 검색용 텍스트 생성
        df_a['text_column'] = df_a['before_text'].fillna('') + ' ' + df_a['after_text'].fillna('')
        df_a['id_column'] = df_a['case_id']
        df_a.to_json(os.path.join(STAGING_DIR, 'A_cases.jsonl'), orient='records', lines=True, force_ascii=False)
    except Exception as e:
        print(f"A_cases.csv 처리 중 오류 발생: {e}")
    
    # 2. B_cases 처리 (B_policies로 이름 변경)
    print("B_cases 파일을 처리 중입니다...")
    try:
        # B_cases.csv 또는 B_cases_restructured.csv 시도
        try:
            df_b = pd.read_csv(os.path.join(SEED_DIR, 'B_cases.csv'), dtype=str)
        except:
            print("B_cases_restructured.csv로 시도합니다...")
            df_b = pd.read_csv(os.path.join(SEED_DIR, 'B_cases_restructured.csv'), dtype=str)
        
        # B_policies 전처리
        df_b['text_column'] = df_b['content'].fillna('')  # content 필드 사용
        df_b['id_column'] = df_b['policy_id']
        df_b.to_json(os.path.join(STAGING_DIR, 'B_policies.jsonl'), orient='records', lines=True, force_ascii=False)
    except Exception as e:
        print(f"B_cases 처리 중 오류 발생: {e}")
    
    # 3. C_laws.csv와 GDPR 데이터 처리
    print("법령 데이터를 처리 중입니다...")
    try:
        # C_laws.csv 처리
        df_c = pd.read_csv(
            os.path.join(SEED_DIR, 'C_cases.csv'),
            dtype=str,
            encoding='utf-8',
            na_values=['', 'nan', 'NaN', 'NULL'],
            keep_default_na=True,
            skipinitialspace=True,
        )
        df_c_processed = preprocess_laws(df_c)
        
        # GDPR 데이터 처리
        try:
            df_gdpr = pd.read_csv(
                os.path.join(SEED_DIR, 'GDPR_10QA_dataset_filtered.csv'),
                dtype=str,
                encoding='utf-8',
                na_values=['', 'nan', 'NaN', 'NULL'],
                keep_default_na=True,
                skipinitialspace=True,
            )
            df_gdpr_processed = preprocess_gdpr(df_gdpr)
            
            # C_laws와 GDPR 데이터 병합
            df_combined = pd.concat([df_c_processed, df_gdpr_processed], ignore_index=True)
            print(f"  - 법령 데이터 {len(df_c_processed)}개와 GDPR 데이터 {len(df_gdpr_processed)}개를 병합했습니다.")
        except Exception as e:
            print(f"GDPR 데이터 처리 중 오류 발생: {e}")
            df_combined = df_c_processed
            print("  - GDPR 데이터 없이 계속합니다.")
        
        # 텍스트 컬럼 생성
        df_combined['text_column'] = df_combined.apply(
            lambda row: f"{row['article_title']} (제{row['article_num']}조) {row['content']}", 
            axis=1
        )
        
        # ID 컬럼 생성
        df_combined['id_column'] = df_combined.apply(
            lambda row: f"{row['law_id']}_{row['article_num']}" if pd.notna(row.get('article_num')) else row['law_id'],
            axis=1
        )
        
        # 결과 저장
        df_combined.to_json(os.path.join(STAGING_DIR, 'C_laws.jsonl'), orient='records', lines=True, force_ascii=False)
        print(f"  - 총 {len(df_combined)}개의 법령 데이터 처리 완료")
    except Exception as e:
        print(f"법령 데이터 처리 중 오류 발생: {e}")
    
    print(f"\n✅ 전처리 완료. 결과가 '{STAGING_DIR}'에 저장되었습니다.")

if __name__ == '__main__':
    main()