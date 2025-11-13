"""
트렌드 리포트 자동 생성 시스템 - 엔트리 포인트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import Config
from app.data_processing import process_data
from app.report_generation import generate_report
from app.weather_data import get_weather_analysis


def main():
    """
    메인 실행 함수
    """
    print("🚀 트렌드 리포트 자동 생성 시작")
    print("=" * 50)
    
    # 1. 데이터 처리 (전처리, 클러스터링, JSON 내보내기)
    print("\n📊 1단계: 데이터 처리 중...")
    phrase_data = process_data(
        csv_path=str(Config.DATA_PATH),
        output_json_path=str(Config.JSON_OUTPUT_PATH),
        month=Config.MONTH
    )
    
    # 1.5. 기상 데이터 분석
    print("\n🌡️ 1.5단계: 기상 데이터 분석 중...")
    try:
        weather_analysis = get_weather_analysis(
            month_str=Config.MONTH,
            api_key=Config.KMA_API_KEY,
            stn_id=Config.KMA_STN_ID,
            years_back=20
        )
        if weather_analysis.get('data_available'):
            print(f"  ✅ {weather_analysis['current_year']}년 {weather_analysis['month']}월 평균기온: {weather_analysis['current_temp']}℃")
            print(f"  📊 20년 평균: {weather_analysis['historical_avg']}℃ (차이: {weather_analysis['diff_from_avg']:+.1f}℃)")
        else:
            print(f"  ⚠️ 기상 데이터를 가져올 수 없습니다: {weather_analysis.get('error', '알 수 없는 오류')}")
            weather_analysis = {}
    except Exception as e:
        print(f"  ⚠️ 기상 데이터 분석 실패: {e}")
        weather_analysis = {}
    
    # 2. 리포트 생성 (템플릿 로드, 태그 처리, PPT 생성)
    print("\n📝 2단계: 리포트 생성 중...")
    generate_report(
        template_path=str(Config.TEMPLATE_PATH),
        output_path=str(Config.OUTPUT_PATH),
        phrase_data=phrase_data,
        month=Config.MONTH,
        gemini_api_key=Config.GEMINI_API_KEY,
        tag_config_path=str(Config.TAG_CONFIG_PATH),
        weather_analysis=weather_analysis
    )
    
    print("\n" + "=" * 50)
    print("✅ 리포트 생성 완료!")
    print(f"📄 출력 파일: {Config.OUTPUT_PATH}")


if __name__ == '__main__':
    main()

