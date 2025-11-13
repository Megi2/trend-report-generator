"""
애플리케이션 설정 파일
"""
import os
from pathlib import Path
from typing import Dict, Any


# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent


class Config:
    """애플리케이션 설정 클래스"""
    
    # 리포트 생성 설정
    MONTH = '10월'
    
    # 파일 경로 설정
    TEMPLATE_PATH = PROJECT_ROOT / 'pptx' / 'template' / 'report_template_251112.pptx'
    OUTPUT_PATH = PROJECT_ROOT / 'pptx' / 'generated' / 'trend_report_output_251112.pptx'
    DATA_PATH = PROJECT_ROOT / 'data' / 'origin_data' / 'twiz_dashboard_oct.csv'
    JSON_OUTPUT_PATH = PROJECT_ROOT / 'data' / 'json' / 'keyword_phrase_mapping_BGE-m3-ko_HDBSCAN_oct.json'
    TAG_CONFIG_PATH = PROJECT_ROOT / 'app' / 'tag_config.json'
    
    # API 설정
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDqOVMzHJ3EHQ8psHCPaCxrf6LEYkEw-Ko')
    GEMINI_MODEL = 'gemini-2.5-flash-lite'
    KMA_API_KEY = os.getenv('KMA_API_KEY', '3BL52U-CTNyS-dlPglzclw')  # 기상청 API 키
    KMA_STN_ID = '108'  # 서울 지점번호
    
    # 데이터 처리 설정
    CLUSTERING_MODEL = 'BAAI/bge-m3'
    MIN_CLUSTER_SIZE = 5
    
    # 차트 생성 설정
    CHART_DPI = 300
    CHART_FONT_FAMILY = 'AppleGothic'  # Mac: 'AppleGothic', Windows: 'Malgun Gothic'
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """
        설정을 딕셔너리로 반환 (하위 호환성)
        
        Returns:
            설정 딕셔너리
        """
        return {
            'month': cls.MONTH,
            'template_path': str(cls.TEMPLATE_PATH),
            'output_path': str(cls.OUTPUT_PATH),
            'data_path': str(cls.DATA_PATH),
            'json_output_path': str(cls.JSON_OUTPUT_PATH),
            'tag_config_path': str(cls.TAG_CONFIG_PATH),
            'gemini_api_key': cls.GEMINI_API_KEY,
            'gemini_model': cls.GEMINI_MODEL,
        }
    
    @classmethod
    def update_from_dict(cls, config_dict: Dict[str, Any]) -> None:
        """
        딕셔너리로부터 설정 업데이트
        
        Args:
            config_dict: 설정 딕셔너리
        """
        if 'month' in config_dict:
            cls.MONTH = config_dict['month']
        if 'template_path' in config_dict:
            cls.TEMPLATE_PATH = Path(config_dict['template_path'])
        if 'output_path' in config_dict:
            cls.OUTPUT_PATH = Path(config_dict['output_path'])
        if 'data_path' in config_dict:
            cls.DATA_PATH = Path(config_dict['data_path'])
        if 'json_output_path' in config_dict:
            cls.JSON_OUTPUT_PATH = Path(config_dict['json_output_path'])
        if 'tag_config_path' in config_dict:
            cls.TAG_CONFIG_PATH = Path(config_dict['tag_config_path'])
        if 'gemini_api_key' in config_dict:
            cls.GEMINI_API_KEY = config_dict['gemini_api_key']
        if 'gemini_model' in config_dict:
            cls.GEMINI_MODEL = config_dict['gemini_model']


# 기본 설정 인스턴스
config = Config()

