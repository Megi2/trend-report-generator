"""
태그 기반 텍스트 생성 모듈
Gemini API를 사용하여 태그별 프롬프트로 텍스트 생성
"""
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from google import genai

from app.config import Config


def clean_markdown(text: str) -> str:
    """
    마크다운 문법 제거
    
    Args:
        text: 원본 텍스트
        
    Returns:
        정제된 텍스트
    """
    # 마크다운 문법 제거
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # # 제거
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** 제거
    text = re.sub(r'__([^_]+)__', r'\1', text)  # __bold__ 제거
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *italic* 제거
    text = re.sub(r'_([^_]+)_', r'\1', text)  # _italic_ 제거
    text = text.strip()
    
    return text


def build_prompt(
    tag_name: str,
    phrase_data: List[Dict[str, Any]],
    month: str,
    config: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    태그별 프롬프트 생성
    
    Args:
        tag_name: 태그 이름
        phrase_data: 프레이즈 데이터
        month: 월 정보
        config: 태그 설정 (프롬프트 템플릿 포함)
        context: 추가 컨텍스트 (차트 데이터, 상위 그룹 등)
        
    Returns:
        완성된 프롬프트
    """
    # 설정에서 프롬프트 템플릿 가져오기
    prompt_template = config.get('prompt_template', '')
    
    # 기본 변수 준비
    format_vars = {
        'month': month,
        'phrase_data': phrase_data,
        'current_year': datetime.now().year
    }
    
    # 컨텍스트에서 추가 변수 추출
    if context:
        format_vars.update(context)
        # insight_title이 context에 있으면 사용
        if 'insight_title' in context:
            format_vars['insight_title'] = context['insight_title']
        
        # 기상 데이터 분석 결과를 포맷팅하여 추가
        if 'weather_analysis' in context:
            weather = context['weather_analysis']
            if weather.get('data_available'):
                format_vars['weather_current_temp'] = weather.get('current_temp', 'N/A')
                format_vars['weather_historical_avg'] = weather.get('historical_avg', 'N/A')
                format_vars['weather_diff_from_avg'] = weather.get('diff_from_avg', 0)
                format_vars['weather_pct_diff_from_avg'] = weather.get('pct_diff_from_avg', 0)
                format_vars['weather_normal_avg'] = weather.get('normal_avg', 'N/A')
                format_vars['weather_diff_from_normal'] = weather.get('diff_from_normal', 0)
                format_vars['weather_pct_diff_from_normal'] = weather.get('pct_diff_from_normal', 0)
                format_vars['weather_rank'] = weather.get('rank', 'N/A')
                format_vars['weather_total_years'] = weather.get('total_years', 20)
                
                # 기온 비교 텍스트 생성
                if weather.get('diff_from_avg', 0) > 0:
                    format_vars['weather_comparison'] = f"평균보다 {abs(weather['diff_from_avg']):.1f}℃ 높았으며"
                elif weather.get('diff_from_avg', 0) < 0:
                    format_vars['weather_comparison'] = f"평균보다 {abs(weather['diff_from_avg']):.1f}℃ 낮았으며"
                else:
                    format_vars['weather_comparison'] = "평균과 유사했으며"
                
                if weather.get('diff_from_normal', 0) > 0:
                    format_vars['weather_normal_comparison'] = f"예년 대비 {abs(weather['diff_from_normal']):.1f}℃ 높았습니다"
                elif weather.get('diff_from_normal', 0) < 0:
                    format_vars['weather_normal_comparison'] = f"예년 대비 {abs(weather['diff_from_normal']):.1f}℃ 낮았습니다"
                else:
                    format_vars['weather_normal_comparison'] = "예년과 유사했습니다"
            else:
                # 데이터 없을 경우 기본값
                format_vars['weather_current_temp'] = 'N/A'
                format_vars['weather_historical_avg'] = 'N/A'
                format_vars['weather_comparison'] = ''
                format_vars['weather_normal_comparison'] = ''
    
    # phrase_data에서 자주 사용되는 변수 자동 추출
    if phrase_data:
        # 상위 프레이즈 추출
        if isinstance(phrase_data, list) and len(phrase_data) > 0:
            # 노이즈 필터링 (프레이즈 이름이 "노이즈"인 항목 제외)
            filtered_phrase_data = [
                p for p in phrase_data 
                if p.get('프레이즈', p.get('phrase', '')) != '노이즈'
            ]
            
            # 노출수 기준 상위 그룹 (노이즈 제외)
            sorted_by_exposure = sorted(
                filtered_phrase_data,
                key=lambda x: x.get('총 노출', x.get('total_impressions', 0)),
                reverse=True
            )[:5]
            format_vars['chart1_top_groups'] = [p.get('프레이즈', p.get('phrase', '')) for p in sorted_by_exposure]
            
            # CTR 기준 상위 그룹 (노이즈 제외)
            sorted_by_ctr = sorted(
                filtered_phrase_data,
                key=lambda x: x.get('평균 CTR', x.get('avg_ctr', 0)),
                reverse=True
            )[:5]
            format_vars['ctr_top_groups'] = [p.get('프레이즈', p.get('phrase', '')) for p in sorted_by_ctr]
            
            # DESCRIPTION1_AREA용 phrase_info_text 생성 (노출수 기준 상위 5개 프레이즈와 키워드, 노이즈 제외)
            phrase_with_keywords = []
            for item in sorted_by_exposure:
                phrase = item.get('프레이즈', item.get('phrase', ''))
                keywords_list = item.get('키워드들', item.get('keywords', []))
                if keywords_list:
                    # 노출수 기준으로 상위 5개 키워드 추출
                    if isinstance(keywords_list[0], dict):
                        keywords = sorted(keywords_list, key=lambda x: x.get('노출수', x.get('impressions', 0)), reverse=True)[:5]
                        keyword_list = [kw.get('키워드', kw.get('keyword', '')) for kw in keywords]
                    else:
                        keyword_list = keywords_list[:5]
                else:
                    keyword_list = []
                
                phrase_with_keywords.append({
                    '프레이즈': phrase,
                    '키워드들': keyword_list
                })
            
            # phrase_info_text 생성 (노트북과 동일하게 chr(10) 사용)
            if phrase_with_keywords:
                format_vars['phrase_info_text'] = chr(10).join([
                    f"- {item['프레이즈']}: {', '.join(item['키워드들']) if item['키워드들'] else '(키워드 정보 없음)'}"
                    for item in phrase_with_keywords
                ])
            else:
                format_vars['phrase_info_text'] = '(프레이즈 정보 없음)'
            
            # DESCRIPTION3_AREA용 phrase_info_text_ctr 생성 (CTR 기준 상위 5개 프레이즈와 키워드, 노이즈 제외)
            phrase_with_keywords_ctr = []
            for item in sorted_by_ctr:
                phrase = item.get('프레이즈', item.get('phrase', ''))
                keywords_list = item.get('키워드들', item.get('keywords', []))
                if keywords_list:
                    # 노출수 기준으로 상위 5개 키워드 추출
                    if isinstance(keywords_list[0], dict):
                        keywords = sorted(keywords_list, key=lambda x: x.get('노출수', x.get('impressions', 0)), reverse=True)[:5]
                        keyword_list = [kw.get('키워드', kw.get('keyword', '')) for kw in keywords]
                    else:
                        keyword_list = keywords_list[:5]
                else:
                    keyword_list = []
                
                phrase_with_keywords_ctr.append({
                    '프레이즈': phrase,
                    '키워드들': keyword_list
                })
            
            # phrase_info_text_ctr 생성 (노트북과 동일하게 chr(10) 사용)
            if phrase_with_keywords_ctr:
                format_vars['phrase_info_text_ctr'] = chr(10).join([
                    f"- {item['프레이즈']}: {', '.join(item['키워드들']) if item['키워드들'] else '(키워드 정보 없음)'}"
                    for item in phrase_with_keywords_ctr
                ])
            else:
                format_vars['phrase_info_text_ctr'] = '(프레이즈 정보 없음)'
    
    # phrase_info_text가 없으면 기본값 설정
    if 'phrase_info_text' not in format_vars:
        format_vars['phrase_info_text'] = '(프레이즈 정보 없음)'
    if 'phrase_info_text_ctr' not in format_vars:
        format_vars['phrase_info_text_ctr'] = '(프레이즈 정보 없음)'
    
    # INSIGHT1_AREA용 insight_title 생성 (노출수 상위와 CTR 상위 프레이즈 비교)
    if phrase_data and isinstance(phrase_data, list) and len(phrase_data) > 0:
        filtered_phrase_data = [
            p for p in phrase_data 
            if p.get('프레이즈', p.get('phrase', '')) != '노이즈'
        ]
        if filtered_phrase_data:
            sorted_by_exposure = sorted(
                filtered_phrase_data,
                key=lambda x: x.get('총 노출', x.get('total_impressions', 0)),
                reverse=True
            )[:5]
            sorted_by_ctr = sorted(
                filtered_phrase_data,
                key=lambda x: x.get('평균 CTR', x.get('avg_ctr', 0)),
                reverse=True
            )[:5]
            
            exposure_phrases = [p.get('프레이즈', p.get('phrase', '')) for p in sorted_by_exposure]
            ctr_phrases = [p.get('프레이즈', p.get('phrase', '')) for p in sorted_by_ctr]
            
            # INSIGHT1_AREA나 INSIGHT_TITLE_AREA를 위한 데이터 준비
            if tag_name in ['INSIGHT1_AREA', 'INSIGHT_TITLE_AREA']:
                format_vars['exposure_phrases'] = exposure_phrases
                format_vars['ctr_phrases'] = ctr_phrases
    
    # insight_title이 없으면 기본값 설정 (INSIGHT1_AREA 처리 시 generate_text_for_tag에서 생성)
    if 'insight_title' not in format_vars:
        format_vars['insight_title'] = None
    elif format_vars.get('insight_title') is None and context and 'insight_title' in context:
        format_vars['insight_title'] = context['insight_title']
    
    # 프롬프트에 변수 치환 (안전하게)
    try:
        prompt = prompt_template.format(**format_vars)
    except KeyError as e:
        # 누락된 변수가 있으면 경고하고 기본값 사용
        print(f"  ⚠️ 프롬프트 변수 누락: {e}, 기본값 사용")
        # 누락된 변수를 빈 문자열로 대체
        import string
        class SafeFormatter(string.Formatter):
            def get_value(self, key, args, kwargs):
                try:
                    return super().get_value(key, args, kwargs)
                except KeyError:
                    return '{' + key + '}'
        formatter = SafeFormatter()
        prompt = formatter.format(prompt_template, **format_vars)
    
    return prompt, format_vars


def generate_text_for_tag(
    tag_name: str,
    phrase_data: List[Dict[str, Any]],
    month: str,
    gemini_api_key: str,
    config: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    태그에 맞는 텍스트 생성
    
    Args:
        tag_name: 태그 이름
        phrase_data: 프레이즈 데이터
        month: 월 정보
        gemini_api_key: Gemini API 키
        config: 태그 설정
        context: 추가 컨텍스트
        
    Returns:
        생성된 텍스트
    """
    # Gemini API 클라이언트 설정
    client = genai.Client(api_key=gemini_api_key)
    
    # INSIGHT1_AREA나 INSIGHT_TITLE_AREA 처리 시 insight_title이 필요하면 먼저 생성
    if tag_name in ['INSIGHT1_AREA', 'INSIGHT_TITLE_AREA']:
        # context나 format_vars에서 insight_title 확인
        if context and 'insight_title' in context:
            pass  # 이미 있음
        else:
            # build_prompt를 먼저 호출해서 데이터 준비
            _, temp_format_vars = build_prompt(tag_name, phrase_data, month, config, context)
            
            # insight_title이 없으면 생성
            if not temp_format_vars.get('insight_title') or temp_format_vars.get('insight_title') == '(인사이트 타이틀 없음)':
                if 'exposure_phrases' in temp_format_vars and 'ctr_phrases' in temp_format_vars:
                    insight_title_prompt = f"""다음은 {month} 트렌드 리포트에서 발견된 데이터입니다:

전체적으로 노출수가 높았던 상위 5개 프레이즈:
{', '.join(temp_format_vars['exposure_phrases'])}

트위즈 고객들이 특히 관심을 보인(CTR이 높은) 상위 5개 프레이즈:
{', '.join(temp_format_vars['ctr_phrases'])}

이 데이터를 바탕으로 트렌드 리포트의 핵심 인사이트를 하나 제시하는 타이틀을 작성해주세요.

작성 가이드:
1. 노출수 상위 프레이즈와 CTR 상위 프레이즈를 비교 분석하여 발견한 핵심 인사이트를 한 문장으로 표현
2. 트위즈 고객들의 특별한 니즈나 트렌드를 드러내는 인사이트여야 함
3. 타이틀 형식으로 작성 (예: "트위즈 고객들은 실용적 뷰티에 집중한다" 또는 "은은하고 데일리한 제품이 트위즈 고객의 선택" 등)
4. 15-25자 정도의 간결한 타이틀
5. {month}의 계절적 특성도 고려

절대 금지사항:
- 수치 데이터(노출수, CTR, % 등)를 직접 언급하지 마세요
- 마크다운 문법(##, ** 등)은 사용하지 말고 순수 텍스트로만 작성
- 옵션을 제시하지 말고 바로 타이틀만 작성
- 설명이나 부연 설명 없이 타이틀만 작성

중요: 타이틀만 작성해주세요. 설명이나 부연 설명은 포함하지 마세요."""
                    
                    print(f"  🤖 인사이트 타이틀 생성 중...")
                    response = client.models.generate_content(
                        model=Config.GEMINI_MODEL,
                        contents=insight_title_prompt
                    )
                    insight_title = response.text.strip()
                    insight_title = clean_markdown(insight_title)
                    # 따옴표 제거
                    insight_title = insight_title.strip('"').strip("'").strip('"').strip("'")
                    
                    # context에 추가하여 다음 호출 시 사용
                    if context is None:
                        context = {}
                    context['insight_title'] = insight_title
                    print(f"  ✅ 인사이트 타이틀 생성 완료: {insight_title}")
    
    # 프롬프트 생성
    prompt, format_vars = build_prompt(tag_name, phrase_data, month, config, context)
    
    # length_guideline이 있으면 프롬프트에 추가
    length_guideline = config.get('length_guideline', {})
    if length_guideline:
        guideline_text = []
        if 'chars_max' in length_guideline:
            guideline_text.append(f"최대 {length_guideline['chars_max']}자")
        if 'chars_approx' in length_guideline:
            guideline_text.append(f"약 {length_guideline['chars_approx']}자")
        if 'lines' in length_guideline:
            guideline_text.append(f"{length_guideline['lines']}줄")
        if 'lines_max' in length_guideline:
            guideline_text.append(f"최대 {length_guideline['lines_max']}줄")
        if guideline_text:
            prompt += f"\n\n길이 제한: {', '.join(guideline_text)}"
    
    # 한국어 출력 지시 추가
    prompt += "\n\n중요: 반드시 한국어로만 작성하세요. 영어나 다른 언어를 사용하지 마세요."
    
    # 텍스트 생성
    print(f"  🤖 텍스트 생성 중: {tag_name}")
    try:
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt
        )
        
        text = response.text.strip()
        
        # 마크다운 제거
        text = clean_markdown(text)
        
        return text
    except Exception as e:
        print(f"  ❌ 텍스트 생성 실패: {e}")
        raise

