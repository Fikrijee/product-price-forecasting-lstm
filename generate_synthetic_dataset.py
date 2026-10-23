import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path
from statistics import pstdev


RANDOM_SEED = 2010
START_DATE = date(2024, 1, 1)
DAY_COUNT = 180
PRODUCTS = [
    ("P001", 19.99, 0.00025),
    ("P002", 34.50, -0.00010),
    ("P003", 7.25, 0.00035),
    ("P004", 52.00, 0.00005),
]
FEATURES = [
    "date",
    "product_id",
    "own_price",
    "competitor_price",
    "discount_rate",
    "stock_level",
    "demand_encoded",
    "season_encoded",
    "promotion_flag",
    "price_ma7",
    "price_ma30",
    "price_volatility",
]


def main():
    random_generator = random.Random(RANDOM_SEED)
    output_path = Path(__file__).with_name("price_data_clean.csv")
    rows = []

    for product_index, (product_id, base_price, daily_trend) in enumerate(PRODUCTS):
        product_prices = []

        for day_offset in range(DAY_COUNT):
            current_date = START_DATE + timedelta(days=day_offset)
            seasonal_effect = (
                0.025 * math.sin(2 * math.pi * day_offset / 45)
                + 0.012 * math.sin(2 * math.pi * day_offset / 180)
            )
            promotion_flag = int((day_offset + product_index * 7) % 50 < 3)
            discount_rate = 0.08 if promotion_flag else 0.0
            own_price = base_price * (
                1
                + daily_trend * day_offset
                + seasonal_effect
                + random_generator.gauss(0, 0.008)
            ) * (1 - discount_rate)
            competitor_price = base_price * 1.025 * (
                1
                + daily_trend * day_offset
                + 0.018 * math.sin(2 * math.pi * day_offset / 60 + product_index)
                + random_generator.gauss(0, 0.01)
            )
            product_prices.append(own_price)

            demand_signal = (
                0.55
                + 0.22 * math.sin(2 * math.pi * day_offset / 30 + product_index)
                + 0.16 * promotion_flag
                + random_generator.gauss(0, 0.06)
            )
            demand_encoded = 0 if demand_signal < 0.45 else 1 if demand_signal < 0.72 else 2
            stock_level = max(
                0,
                int(90 - 32 * demand_signal + random_generator.randint(-12, 12)),
            )
            recent_prices = product_prices[-30:]

            rows.append(
                {
                    "date": current_date.isoformat(),
                    "product_id": product_id,
                    "own_price": round(own_price, 4),
                    "competitor_price": round(competitor_price, 4),
                    "discount_rate": discount_rate,
                    "stock_level": stock_level,
                    "demand_encoded": demand_encoded,
                    "season_encoded": (current_date.month % 12) // 3,
                    "promotion_flag": promotion_flag,
                    "price_ma7": round(sum(product_prices[-7:]) / len(product_prices[-7:]), 4),
                    "price_ma30": round(sum(recent_prices) / len(recent_prices), 4),
                    "price_volatility": round(pstdev(recent_prices), 4),
                }
            )

    with output_path.open("w", newline="", encoding="utf-8") as dataset_file:
        writer = csv.DictWriter(dataset_file, fieldnames=FEATURES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic rows to {output_path}")


if __name__ == "__main__":
    main()