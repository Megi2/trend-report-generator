"""
기상청 API를 통한 기상 데이터 수집 및 분석 모듈
"""
import requests
import pandas as pd
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class WeatherDataAnalyzer:
    """기상 데이터 분석 클래스"""
    
    def __init__(self, api_key: str, stn_id: str = "108", cache_dir: Optional[Path] = None):
        """
        초기화
        
        Args:
            api_key: 기상청 API 인증키
            stn_id: 지점번호 (108: 서울)
            cache_dir: 캐시 파일 저장 디렉토리
        """
        self.api_key = api_key
        self.stn_id = stn_id
        self.base_url = "https://apihub.kma.go.kr/api/typ01/url/sts_ta.php"
        self.cache_dir = cache_dir or Path(__file__).parent.parent / 'data' / 'weather'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f'weather_data_stn{stn_id}.csv'
    
    def fetch_monthly_temp(self, year: int, month: int, max_retries: int = 3) -> Optional[pd.DataFrame]:
        """
        특정 년월의 월평균기온 데이터 가져오기
        
        Args:
            year: 연도
            month: 월 (1-12)
            max_retries: 최대 재시도 횟수
            
        Returns:
            DataFrame 또는 None (데이터 없을 경우)
        """
        tm = f"{year}{month:02d}"
        url = f"{self.base_url}?tm1={tm}&tm2={tm}&stn_id={self.stn_id}&help=0&disp=1&authKey={self.api_key}"
        
        # 재시도 로직
        res = None
        for attempt in range(max_retries):
            try:
                res = requests.get(url, timeout=30)  # 타임아웃 30초로 증가
                res.raise_for_status()
                break  # 성공하면 루프 탈출
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2초, 4초, 6초 대기
                    print(f"  ⚠️ {year}년 {month}월 데이터 요청 실패 (시도 {attempt + 1}/{max_retries}), {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"  ⚠️ {year}년 {month}월 데이터 가져오기 실패: {e}")
                    return None
            except Exception as e:
                print(f"  ⚠️ {year}년 {month}월 데이터 가져오기 실패: {e}")
                return None
        
        if res is None:
            return None
        
        try:
            # 응답 파싱
            raw = res.text.strip().split("\n")
            
            if len(raw) < 2:
                return None
            
            # 첫 번째 라인이 #으로 시작하는 헤더인 경우 # 제거
            header_line = raw[0].strip()
            if header_line.startswith('#'):
                header_line = header_line[1:].strip()
            
            header = header_line.split()
            values = raw[1].split()
            
            # 헤더와 값의 개수가 맞지 않으면 더 짧은 쪽에 맞춰서 처리
            if len(header) != len(values):
                min_len = min(len(header), len(values))
                header = header[:min_len]
                values = values[:min_len]
            
            df = pd.DataFrame([values], columns=header)
            
            # 주요 지표 float 변환
            if "TA_MAVG" in df.columns:
                df["TA_MAVG"] = df["TA_MAVG"].astype(float)
            
            return df
            
        except Exception as e:
            print(f"⚠️ {year}년 {month}월 데이터 파싱 실패: {e}")
            return None
    
    def load_or_fetch_all_data(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        CSV 캐시에서 데이터를 로드하거나, 없으면 API로 전체 데이터를 가져와서 저장
        
        Args:
            force_refresh: True면 캐시를 무시하고 API에서 새로 가져오기
            
        Returns:
            DataFrame (TM, TA_MAVG 컬럼 포함)
        """
        # 캐시 파일이 있고 강제 새로고침이 아니면 로드
        if self.cache_file.exists() and not force_refresh:
            try:
                df = pd.read_csv(self.cache_file)
                print(f"  📂 캐시에서 기상 데이터 로드: {len(df)}개 레코드")
                return df
            except Exception as e:
                print(f"  ⚠️ 캐시 파일 읽기 실패: {e}, API에서 새로 가져옵니다.")
        
        # API에서 전체 데이터 가져오기 (2000년 1월 ~ 현재)
        print(f"  🌐 API에서 기상 데이터 수집 중... (처음 실행 시 시간이 걸릴 수 있습니다)")
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        results = []
        total_requests = (current_year - 2000) * 12 + current_month
        
        for year in range(2000, current_year + 1):
            for month in range(1, 13):
                # 현재 년월 이후는 스킵
                if year == current_year and month > current_month:
                    break
                
                df = self.fetch_monthly_temp(year, month)
                if df is not None and "TA_MAVG" in df.columns:
                    results.append(df[["TM", "TA_MAVG"]])
                
                # 진행 상황 출력
                if len(results) % 12 == 0:
                    print(f"  📊 진행: {len(results)}/{total_requests}개 월 데이터 수집 완료")
                
                # 요청 간 딜레이 추가 (API 서버 부하 방지)
                time.sleep(0.3)  # 0.3초 대기
        
        if not results:
            return pd.DataFrame(columns=["TM", "TA_MAVG"])
        
        df_all = pd.concat(results, ignore_index=True)
        
        # CSV로 저장
        df_all.to_csv(self.cache_file, index=False)
        print(f"  💾 기상 데이터 캐시 저장 완료: {self.cache_file} ({len(df_all)}개 레코드)")
        
        return df_all
    
    def get_historical_data(self, month: int, years_back: int = 20, force_refresh: bool = False) -> pd.DataFrame:
        """
        과거 N년치 해당 월의 기온 데이터 가져오기
        
        Args:
            month: 월 (1-12)
            years_back: 몇 년 전까지 가져올지 (기본 20년)
            force_refresh: True면 캐시를 무시하고 API에서 새로 가져오기
            
        Returns:
            DataFrame (TM, TA_MAVG 컬럼 포함)
        """
        # 전체 데이터 로드 (캐시 또는 API)
        df_all = self.load_or_fetch_all_data(force_refresh=force_refresh)
        
        if df_all.empty:
            return pd.DataFrame(columns=["TM", "TA_MAVG"])
        
        # 해당 월만 필터링
        df_month = df_all[df_all["TM"].str.endswith(f"{month:02d}")].copy()
        
        # 최근 N년치만 선택
        if years_back:
            current_year = datetime.now().year
            min_year = current_year - years_back + 1
            df_month["year"] = df_month["TM"].str[:4].astype(int)
            df_month = df_month[df_month["year"] >= min_year].copy()
            df_month = df_month.drop(columns=["year"])
        
        return df_month.reset_index(drop=True)
    
    def analyze_temperature(self, month: int, current_year: Optional[int] = None, years_back: int = 20) -> Dict[str, Any]:
        """
        기온 데이터 분석
        
        Args:
            month: 월 (1-12)
            current_year: 분석할 연도 (None이면 현재 연도)
            years_back: 몇 년 전까지 분석할지 (기본 20년)
            
        Returns:
            분석 결과 딕셔너리
        """
        if current_year is None:
            current_year = datetime.now().year
        
        # 과거 데이터 가져오기 (요청 간 딜레이 추가)
        df = self.get_historical_data(month, years_back)
        
        if df.empty or "TA_MAVG" not in df.columns:
            return {
                "error": "데이터를 가져올 수 없습니다.",
                "current_year": current_year,
                "month": month
            }
        
        # 현재 연도 데이터 추출
        current_tm = f"{current_year}{month:02d}"
        current_data = df[df["TM"] == current_tm]
        
        if current_data.empty:
            return {
                "error": f"{current_year}년 {month}월 데이터가 없습니다.",
                "current_year": current_year,
                "month": month,
                "historical_avg": df["TA_MAVG"].mean() if not df.empty else None
            }
        
        current_temp = current_data["TA_MAVG"].iloc[0]
        
        # 전체 평균 (20년치)
        historical_avg = df["TA_MAVG"].mean()
        
        # 예년 평균 (1991-2020 기준, 30년 평균이지만 사용 가능한 데이터로 계산)
        # 실제로는 사용 가능한 모든 데이터의 평균을 예년 평균으로 사용
        normal_avg = df["TA_MAVG"].mean()  # 사용 가능한 데이터의 평균
        
        # 편차 계산
        diff_from_avg = current_temp - historical_avg
        diff_from_normal = current_temp - normal_avg
        
        # 백분율 차이
        pct_diff_from_avg = (diff_from_avg / historical_avg * 100) if historical_avg != 0 else 0
        pct_diff_from_normal = (diff_from_normal / normal_avg * 100) if normal_avg != 0 else 0
        
        # 최고/최저 기온
        max_temp = df["TA_MAVG"].max()
        min_temp = df["TA_MAVG"].min()
        
        # 순위 (높은 순)
        df_sorted = df.sort_values("TA_MAVG", ascending=False).reset_index(drop=True)
        rank = df_sorted[df_sorted["TM"] == current_tm].index[0] + 1 if not df_sorted[df_sorted["TM"] == current_tm].empty else None
        total_years = len(df)
        
        return {
            "current_year": current_year,
            "month": month,
            "current_temp": round(current_temp, 1),
            "historical_avg": round(historical_avg, 1),
            "normal_avg": round(normal_avg, 1),
            "diff_from_avg": round(diff_from_avg, 1),
            "diff_from_normal": round(diff_from_normal, 1),
            "pct_diff_from_avg": round(pct_diff_from_avg, 1),
            "pct_diff_from_normal": round(pct_diff_from_normal, 1),
            "max_temp": round(max_temp, 1),
            "min_temp": round(min_temp, 1),
            "rank": rank,
            "total_years": total_years,
            "data_available": True
        }


def get_weather_analysis(month_str: str, api_key: str, stn_id: str = "108", years_back: int = 20) -> Dict[str, Any]:
    """
    월 문자열로부터 기온 분석 수행 (편의 함수)
    
    Args:
        month_str: 월 문자열 (예: "10월", "10")
        api_key: 기상청 API 인증키
        stn_id: 지점번호
        years_back: 몇 년 전까지 분석할지
        
    Returns:
        분석 결과 딕셔너리
    """
    # 월 문자열을 숫자로 변환
    month = int(month_str.replace("월", "").strip())
    
    analyzer = WeatherDataAnalyzer(api_key, stn_id)
    current_year = datetime.now().year
    
    return analyzer.analyze_temperature(month, current_year, years_back)

