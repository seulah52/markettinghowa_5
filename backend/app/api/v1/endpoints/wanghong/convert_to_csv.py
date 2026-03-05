import json
import csv

def json_to_csv():
    try:
        with open('influencers.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            print("데이터가 비어 있습니다.")
            return

        # CSV 파일 생성
        with open('wanghong_100_list.csv', 'w', encoding='utf-8-sig', newline='') as f:
            # 컬럼 순서 정의
            fieldnames = ['name', 'id', 'followers', 'growth_amount', 'growth_rate', 'score', 'avatar', 'description']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                # 필요한 데이터만 추출 (DictWriter는 fieldnames에 없는 키는 무시하거나 에러를 낼 수 있음)
                clean_row = {field: row.get(field, '') for field in fieldnames}
                writer.writerow(clean_row)
        
        print(f"✅ 성공: 100명의 왕홍 데이터가 'wanghong_100_list.csv'로 저장되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    json_to_csv()
