from app import app, mysql

with app.app_context():
    try:
        # Test database connection
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        
        if result:
            print("✅ تم الاتصال بقاعدة البيانات بنجاح!")
            
            # Test if user table exists
            cur = mysql.connection.cursor()
            cur.execute("SHOW TABLES LIKE 'user'")
            table_exists = cur.fetchone()
            cur.close()
            
            if table_exists:
                print("✅ جدول 'user' موجود في قاعدة البيانات")
                
                # Show table structure
                cur = mysql.connection.cursor()
                cur.execute("DESCRIBE user")
                columns = cur.fetchall()
                cur.close()
                
                print("📋 هيكل جدول 'user':")
                for column in columns:
                    print(f"  - {column[0]} ({column[1]})")
            else:
                print("❌ جدول 'user' غير موجود في قاعدة البيانات")
                
    except Exception as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}") 