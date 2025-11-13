"""
데이터 전처리, 인코딩, 클러스터링, 대표 프레이즈 추출, JSON 내보내기
"""
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# 클러스터링 관련 (필요시 import)
# from sentence_transformers import SentenceTransformer
# import umap
# import hdbscan


def load_data(csv_path: str) -> pd.DataFrame:
    """
    CSV 데이터 로드
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        DataFrame
    """
    df = pd.read_csv(csv_path)
    print(f"✅ 데이터 로드 완료: {len(df)}개 행")
    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터 전처리
    
    Args:
        df: 원본 DataFrame
        
    Returns:
        전처리된 DataFrame
    """
    # 필요한 전처리 수행
    # 예: 결측치 처리, 데이터 타입 변환 등
    print("✅ 데이터 전처리 완료")
    return df


def encode_keywords(keywords: List[str], model_name: str = 'BAAI/bge-m3') -> np.ndarray:
    """
    키워드를 벡터로 인코딩
    
    Args:
        keywords: 키워드 리스트
        model_name: 사용할 모델명
        
    Returns:
        인코딩된 벡터 배열
    """
    # TODO: SentenceTransformer를 사용한 인코딩 구현
    # model = SentenceTransformer(model_name)
    # embeddings = model.encode(keywords)
    # return embeddings
    print(f"✅ 키워드 인코딩 완료: {len(keywords)}개")
    return np.array([])  # 임시


def cluster_keywords(embeddings: np.ndarray, min_cluster_size: int = 5) -> np.ndarray:
    """
    키워드를 클러스터링
    
    Args:
        embeddings: 인코딩된 벡터 배열
        min_cluster_size: 최소 클러스터 크기
        
    Returns:
        클러스터 레이블 배열
    """
    # TODO: UMAP + HDBSCAN을 사용한 클러스터링 구현
    # reducer = umap.UMAP(n_components=10, random_state=42)
    # reduced = reducer.fit_transform(embeddings)
    # clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
    # labels = clusterer.fit_predict(reduced)
    # return labels
    print("✅ 클러스터링 완료")
    return np.array([])  # 임시


def extract_representative_phrases(
    df: pd.DataFrame,
    cluster_labels: np.ndarray,
    keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    각 클러스터에서 대표 프레이즈 추출
    
    Args:
        df: 원본 데이터프레임
        cluster_labels: 클러스터 레이블
        keywords: 키워드 리스트
        
    Returns:
        프레이즈별 데이터 리스트
    """
    # TODO: 클러스터별로 대표 프레이즈 추출 로직 구현
    # 각 클러스터의 키워드들을 그룹화하고
    # 노출수/클릭수 기준으로 대표 프레이즈 선정
    
    phrase_data = []
    print("✅ 대표 프레이즈 추출 완료")
    return phrase_data


def export_to_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    데이터를 JSON 파일로 내보내기
    
    Args:
        data: 내보낼 데이터
        output_path: 출력 파일 경로
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON 내보내기 완료: {output_path}")


def process_data(
    csv_path: str,
    output_json_path: str,
    month: str = None
) -> List[Dict[str, Any]]:
    """
    전체 데이터 처리 파이프라인
    
    Args:
        csv_path: 입력 CSV 파일 경로
        output_json_path: 출력 JSON 파일 경로
        month: 월 정보 (선택사항)
        
    Returns:
        처리된 프레이즈 데이터 리스트
    """
    print(f"📂 데이터 파일: {csv_path}")
    
    # 1. 데이터 로드
    df = load_data(csv_path)
    
    # 2. 데이터 전처리
    df_processed = preprocess_data(df)
    
    # 3. 키워드 추출 및 인코딩
    # keywords = df_processed['소재명'].unique().tolist()
    # embeddings = encode_keywords(keywords)
    
    # 4. 클러스터링
    # cluster_labels = cluster_keywords(embeddings)
    
    # 5. 대표 프레이즈 추출
    # phrase_data = extract_representative_phrases(df_processed, cluster_labels, keywords)
    
    # 임시: 기존 JSON 파일이 있으면 로드
    if Path(output_json_path).exists():
        print(f"📂 기존 JSON 파일 로드: {output_json_path}")
        with open(output_json_path, 'r', encoding='utf-8') as f:
            phrase_data = json.load(f)
    else:
        # 새로 생성 (실제 구현 필요)
        phrase_data = []
        print("⚠️ JSON 파일이 없습니다. 클러스터링을 수행해야 합니다.")
    
    # 6. JSON 내보내기
    if phrase_data:
        export_to_json(phrase_data, output_json_path)
    
    return phrase_data

