import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app import models
from app.auth import get_password_hash


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        admin = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin:
            admin = models.User(
                username="admin",
                full_name="系统管理员",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role=models.UserRole.ADMIN,
                phone="13800000000",
                is_active=True,
            )
            db.add(admin)
        
        regulator = db.query(models.User).filter(models.User.username == "regulator").first()
        if not regulator:
            regulator = models.User(
                username="regulator",
                full_name="市场监管员",
                email="regulator@example.com",
                hashed_password=get_password_hash("regulator123"),
                role=models.UserRole.REGULATOR,
                phone="13800000001",
                is_active=True,
            )
            db.add(regulator)
        
        verifier = db.query(models.User).filter(models.User.username == "verifier").first()
        if not verifier:
            verifier = models.User(
                username="verifier",
                full_name="检定员",
                email="verifier@example.com",
                hashed_password=get_password_hash("verifier123"),
                role=models.UserRole.VERIFIER,
                phone="13800000002",
                is_active=True,
            )
            db.add(verifier)
        
        merchant_user = db.query(models.User).filter(models.User.username == "merchant").first()
        if not merchant_user:
            merchant_user = models.User(
                username="merchant",
                full_name="商户用户",
                email="merchant@example.com",
                hashed_password=get_password_hash("merchant123"),
                role=models.UserRole.MERCHANT,
                phone="13800000003",
                is_active=True,
            )
            db.add(merchant_user)
        
        test_merchant = db.query(models.Merchant).filter(models.Merchant.merchant_code == "M001").first()
        if not test_merchant:
            test_merchant = models.Merchant(
                merchant_code="M001",
                name="测试商户有限公司",
                address="北京市朝阳区测试路123号",
                contact_person="张经理",
                contact_phone="13900000001",
                business_type="零售",
                license_number="91110000MA000TEST",
                is_active=True,
            )
            db.add(test_merchant)
            db.flush()
            
            merchant_user.merchant_id = test_merchant.id
            
            scale1 = models.Scale(
                scale_number="S20240001",
                merchant_id=test_merchant.id,
                scale_type="电子台秤",
                manufacturer="衡器制造有限公司",
                model="TCS-150",
                serial_number="SN20240001",
                max_capacity=150.0,
                min_capacity=0.5,
                accuracy_class="III",
                verification_interval_months=12,
                status=models.ScaleStatus.ACTIVE,
                installation_location="一楼收银台",
            )
            db.add(scale1)
            
            scale2 = models.Scale(
                scale_number="S20240002",
                merchant_id=test_merchant.id,
                scale_type="电子计价秤",
                manufacturer="衡器制造有限公司",
                model="ACS-30",
                serial_number="SN20240002",
                max_capacity=30.0,
                min_capacity=0.1,
                accuracy_class="III",
                verification_interval_months=12,
                status=models.ScaleStatus.ACTIVE,
                installation_location="水果区",
            )
            db.add(scale2)
        
        weights_data = [
            ("W001", 1.0, "kg", "F2"),
            ("W002", 2.0, "kg", "F2"),
            ("W003", 5.0, "kg", "F2"),
            ("W004", 10.0, "kg", "F2"),
            ("W005", 20.0, "kg", "F2"),
            ("W006", 50.0, "kg", "F2"),
            ("W007", 100.0, "kg", "M1"),
        ]
        
        for code, value, unit, acc_class in weights_data:
            existing = db.query(models.StandardWeight).filter(
                models.StandardWeight.weight_code == code
            ).first()
            if not existing:
                weight = models.StandardWeight(
                    weight_code=code,
                    nominal_value=value,
                    unit=unit,
                    accuracy_class=acc_class,
                    is_available=True,
                )
                db.add(weight)
        
        db.commit()
        print("数据库初始化完成！")
        print("默认用户账号：")
        print("  管理员 - admin / admin123")
        print("  市场监管员 - regulator / regulator123")
        print("  检定员 - verifier / verifier123")
        print("  商户 - merchant / merchant123")
        
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
