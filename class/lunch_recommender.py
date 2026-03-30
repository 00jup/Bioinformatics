# 점심 메뉴 추천 프로그램

import random

lunch_menus = [
    "김밥",
    "라면",
    "돈까스",
    "치킨",
    "쌀국수",
    "우동",
    "비빔밥",
    "순두부찌개",
    "불고기덮밥",
    "마라탕",
    "피자",
    "햄버거",
    "김치찌개",
    "된장찌개",
    "곰탕",
    "국밥",
    "닭갈비",
    "삼겹살",
    "제육볶음",
    "스시",
]


def recommend_lunch():
    """랜덤으로 점심 메뉴 추천"""
    return random.choice(lunch_menus)


def recommend_by_category(category):
    """카테고리별 메뉴 추천"""
    categories = {
        "한식": ["김밥", "비빔밥", "순두부찌개", "김치찌개", "국밥"],
        "면류": ["라면", "우동", "쌀국수"],
        "고기": ["돈까스", "불고기덮밥", "닭갈비", "삼겹살", "제육볶음"],
        "찌개": ["순두부찌개", "김치찌개", "된장찌개", "마라탕"],
        "양식": ["피자", "햄버거"],
    }
    
    if category in categories:
        return random.choice(categories[category])
    else:
        return "해당 카테고리가 없습니다."


# 실행 예시
if __name__ == "__main__":
    print("=== 점심 메뉴 추천 프로그램 ===\n")
    
    choice = input("1. 랜덤 추천  2. 카테고리 선택\n선택 (1 또는 2): ")
    
    if choice == "1":
        menu = recommend_lunch()
        print(f"\n오늘의 점심 메뉴: {menu} 🍽️")
    elif choice == "2":
        print("\n카테고리: 한식, 면류, 고기, 찌개, 양식")
        category = input("카테고리를 선택하세요: ")
        menu = recommend_by_category(category)
        print(f"\n추천 메뉴: {menu} 🍽️")
    else:
        print("잘못된 입력입니다.")
