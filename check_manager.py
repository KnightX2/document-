import mysql.connector

# إعدادات قاعدة البيانات
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'document_archive'
}

def check_and_add_manager():
    try:
        # الاتصال بقاعدة البيانات
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        
        # التحقق من وجود حساب المدير
        cur.execute("SELECT * FROM user WHERE Email = 'manager@example.com'")
        manager = cur.fetchone()
        
        if not manager:
            # إضافة حساب المدير
            cur.execute("""
                INSERT INTO user (Name, Email, Password, RoleID) 
                VALUES ('Manager', 'manager@example.com', 'manager123', 2)
            """)
            conn.commit()
            print("تم إضافة حساب المدير بنجاح!")
            print("البريد الإلكتروني: manager@example.com")
            print("كلمة المرور: manager123")
        else:
            print("حساب المدير موجود بالفعل!")
            print("البريد الإلكتروني: manager@example.com")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"خطأ: {e}")

if __name__ == "__main__":
    check_and_add_manager() 