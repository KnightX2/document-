from app import app, mysql
from flask import render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename

# إعداد مسار حفظ الملفات المرفقة
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# الصفحة الرئيسية (تحويل تلقائي لصفحة الدخول)
@app.route('/')
def home():
    return redirect(url_for('login'))

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE Email=%s AND Password=%s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            # Store user information in session
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            session['role_id'] = user[3]
            
            # Check if user is admin
            is_admin = False
            try:
                role_id = user[3]  # Assuming RoleID is at index 3
                if isinstance(role_id, int) and role_id == 1:
                    is_admin = True
                elif isinstance(role_id, str) and 'admin' in role_id.lower():
                    is_admin = True
                elif 'admin' in str(user[1]).lower():  # Check username
                    is_admin = True
            except:
                pass
            
            # Check if user is manager
            is_manager = False
            if email.lower() == 'manager@example.com':
                is_manager = True

            # Check if user is employee@example.com
            is_employee = False
            if email.lower() == 'employee@example.com':
                is_employee = True

            session['is_admin'] = is_admin
            session['is_manager'] = is_manager
            session['is_employee'] = is_employee
            flash("تم تسجيل الدخول بنجاح!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("بيانات غير صحيحة", "error")

    return render_template('login.html')

# تسجيل الدخول كزائر
@app.route('/guest-login', methods=['POST'])
def guest_login():
    session['user_id'] = 'guest'
    session['user_name'] = 'Guest'
    session['is_admin'] = False
    session['is_guest'] = True
    flash("Logged in as guest successfully!", "success")
    return redirect(url_for('dashboard'))

# لوحة التحكم
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_name = session.get('user_name', 'User')
    is_admin = session.get('is_admin', False)
    is_guest = session.get('is_guest', False)
    is_manager = session.get('is_manager', False)
    is_employee = session.get('is_employee', False)
    
    return render_template('dashboard.html', user_name=user_name, is_admin=is_admin, is_guest=is_guest, is_manager=is_manager, is_employee=is_employee)

# إضافة وثيقة جديدة
@app.route('/add-document', methods=['GET', 'POST'])
def add_document():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT SectionID, SectionName FROM section")
    sections = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        document_name = request.form['document_name']
        title = request.form['title']
        document_type = request.form['document_type']
        date = request.form['date']
        entity_type = request.form['entity_type']
        description = request.form['description']
        section_id = request.form['section_id']
        is_visible = 1 if 'is_visible' in request.form else 0

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO document 
            (DocumentName, Title, Date, FilePath, Description, DocumentType, SectionID, IsVisible, EntityType)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            document_name, title, date, '', description, document_type, section_id, is_visible, entity_type
        ))
        mysql.connection.commit()
        cur.close()

        flash("Document added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_document.html', sections=sections)

# البحث عن وثيقة
@app.route('/search-document', methods=['GET', 'POST'])
def search_document():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is admin, manager, employee, or guest
    if not (session.get('is_admin', False) or session.get('is_manager', False) or session.get('is_employee', False) or session.get('is_guest', False)):
        flash("Access denied. Login required.", "error")
        return redirect(url_for('dashboard'))

    documents = []
    search_performed = False
    
    if request.method == 'POST':
        search_performed = True
        document_id = request.form.get('document_id', '')
        title = request.form.get('title', '')
        
        try:
            cur = mysql.connection.cursor()
            
            # Build search query
            query = "SELECT * FROM document WHERE 1=1"
            params = []
            
            if document_id:
                query += " AND DocumentID LIKE %s"
                params.append(f"%{document_id}%")
            
            if title:
                query += " AND Title LIKE %s"
                params.append(f"%{title}%")
            
            if params:
                cur.execute(query, params)
                documents = cur.fetchall()
            else:
                # If no search criteria, show all documents
                cur.execute("SELECT * FROM document")
                documents = cur.fetchall()
                
            cur.close()
            
            if not documents:
                flash("No documents found matching your search criteria.", "info")
                
        except Exception as e:
            flash(f"Search error: {str(e)}", "error")
            print(f"Search error: {e}")

    return render_template('search_document.html', documents=documents, search_performed=search_performed)

@app.route('/edit-document/<int:document_id>', methods=['GET', 'POST'])
def edit_document(document_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    if request.method == 'POST':
        # تحديث بيانات الوثيقة
        new_document_id = request.form['document_id']
        document_name = request.form['document_name']
        title = request.form['title']
        document_type = request.form['document_type']
        date = request.form['date']
        entity_type = request.form['entity_type']
        description = request.form['description']
        from_section = request.form.get('from_section', '')
        section_id = request.form['section_id']
        is_visible = 1 if 'is_visible' in request.form else 0

        try:
            # تحديث الوثيقة
            cur.execute("""
                UPDATE document 
                SET DocumentID = %s, DocumentName = %s, Title = %s, Date = %s, 
                    Description = %s, DocumentType = %s, SectionID = %s, IsVisible = %s, 
                    EntityType = %s, FromSection = %s
                WHERE DocumentID = %s
            """, (
                new_document_id, document_name, title, date, description, 
                document_type, section_id, is_visible, entity_type, from_section, document_id
            ))
            mysql.connection.commit()
            flash("Document updated successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Error updating document: {str(e)}", "error")
            mysql.connection.rollback()

    # جلب بيانات الوثيقة حسب ID
    cur.execute("SELECT * FROM document WHERE DocumentID = %s", (document_id,))
    document = cur.fetchone()

    if not document:
        flash("Document not found.", "error")
        return redirect(url_for('dashboard'))

    # جلب الأقسام لعرضهم بالواجهة
    cur.execute("SELECT SectionID, SectionName FROM section")
    sections = cur.fetchall()
    cur.close()

    return render_template('edit_document.html', document=document, sections=sections)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route('/manage-departments', methods=['GET', 'POST'])
def manage_departments():
    if 'user_id' not in session or not session.get('is_admin', False):
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')
        section_id = request.form['section_id']
        section_name = request.form.get('section_name')
        cur = mysql.connection.cursor()
        
        if action == 'add':
            cur.execute("SELECT * FROM section WHERE SectionID = %s", (section_id,))
            if cur.fetchone():
                flash("Department ID already exists!", "error")
            else:
                cur.execute("INSERT INTO section (SectionID, SectionName) VALUES (%s, %s)", (section_id, section_name))
                mysql.connection.commit()
                flash("Department added successfully!", "success")
        
        elif action == 'update':
            cur.execute("SELECT * FROM section WHERE SectionID = %s", (section_id,))
            if not cur.fetchone():
                flash("Department not found!", "error")
            else:
                cur.execute("UPDATE section SET SectionName = %s WHERE SectionID = %s", (section_name, section_id))
                mysql.connection.commit()
                flash("Department updated successfully!", "success")
        
        elif action == 'delete':
            cur.execute("SELECT * FROM section WHERE SectionID = %s", (section_id,))
            if not cur.fetchone():
                flash("Department not found!", "error")
            else:
                cur.execute("DELETE FROM section WHERE SectionID = %s", (section_id,))
                mysql.connection.commit()
                flash("Department deleted successfully!", "success")
        
        cur.close()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM section ORDER BY SectionName")
    sections = cur.fetchall()
    cur.close()
    return render_template('manage_departments.html', sections=sections)

def manager_only():
    if ('is_manager' not in session or not session['is_manager']) and ('is_employee' not in session or not session['is_employee']):
        flash('هذه الصفحة متاحة فقط للمدير أو الموظف المصرح له.', 'error')
        return False
    return True

@app.route('/manager/add-document', methods=['GET', 'POST'])
def manager_add_document():
    if not manager_only():
        return redirect(url_for('dashboard'))
    
    # جلب الأقسام من قاعدة البيانات
    cur = mysql.connection.cursor()
    cur.execute("SELECT SectionID, SectionName FROM section ORDER BY SectionName")
    sections = cur.fetchall()
    cur.close()
    
    auto_id = 'DOC-20240620-001'  # يمكن توليده ديناميكياً
    return render_template('manager/add_document.html', auto_id=auto_id, sections=sections)

@app.route('/manager/edit-document', methods=['GET', 'POST'])
def manager_edit_document():
    if not manager_only():
        return redirect(url_for('dashboard'))
    
    # جلب الأقسام من قاعدة البيانات
    cur = mysql.connection.cursor()
    cur.execute("SELECT SectionID, SectionName FROM section ORDER BY SectionName")
    sections = cur.fetchall()
    cur.close()
    
    # بيانات افتراضية للاختبار
    document = {
        'DocumentID': 'DOC-20240620-001',
        'Title': 'عنوان افتراضي',
        'Date': '2024-06-20',
        'DocumentType': 'report',
        'Department': 'it',
        'Description': 'وصف افتراضي',
        'FilePath': 'uploads/sample.pdf',
    }
    return render_template('manager/edit_document.html', document=document, sections=sections)

@app.route('/manager/delete-document', methods=['GET', 'POST'])
def manager_delete_document():
    if not manager_only():
        return redirect(url_for('dashboard'))
    return render_template('manager/delete_document.html')

@app.route('/manager/view-document', methods=['GET', 'POST'])
def manager_view_document():
    if not manager_only():
        return redirect(url_for('dashboard'))
    document = None
    not_found = False
    document_id = request.form.get('document_id') if request.method == 'POST' else ''
    if document_id:
        if document_id == 'notfound':
            not_found = True
        else:
            document = {
                'DocumentID': document_id,
                'Title': 'عنوان افتراضي',
                'Date': '2024-06-20',
                'DocumentType': 'report',
                'Department': 'it',
                'Description': 'وصف افتراضي',
                'FilePath': 'uploads/sample.pdf',
            }
    return render_template('manager/view_document.html', document=document, not_found=not_found, document_id=document_id)

@app.route('/manager/record-outgoing', methods=['GET', 'POST'])
def manager_record_outgoing():
    if not manager_only():
        return redirect(url_for('dashboard'))
    return render_template('manager/record_outgoing.html')

@app.route('/manager/record-incoming', methods=['GET', 'POST'])
def manager_record_incoming():
    if not manager_only():
        return redirect(url_for('dashboard'))
    return render_template('manager/record_incoming.html')

@app.route('/manager/search-document', methods=['GET', 'POST'])
def manager_search_document():
    if not manager_only():
        return redirect(url_for('dashboard'))
    documents = []
    if request.method == 'POST':
        # بيانات افتراضية للنتائج
        documents = [
            {'DocumentID': 'DOC-20240620-001', 'Title': 'عنوان افتراضي', 'DocumentType': 'report', 'Department': 'it', 'Date': '2024-06-20'},
            {'DocumentID': 'DOC-20240620-002', 'Title': 'وثيقة أخرى', 'DocumentType': 'memo', 'Department': 'hr', 'Date': '2024-06-19'},
        ]
    return render_template('manager/search_document.html', documents=documents)

@app.route('/create-backup', methods=['GET', 'POST'])
def create_backup():
    if 'user_id' not in session or not session.get('is_admin', False):
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # Get form data
            backup_name = request.form['backup_name']
            backup_type = request.form['backup_type']
            compression = request.form['compression']
            encryption = request.form['encryption']
            schedule_type = request.form['schedule_type']
            backup_time = request.form['backup_time']
            retention_days = request.form.get('retention_days', 30)
            max_backups = request.form.get('max_backups', 10)
            backup_notes = request.form.get('backup_notes', '')
            
            # Get selected data types
            backup_users = 'backup_users' in request.form
            backup_documents = 'backup_documents' in request.form
            backup_departments = 'backup_departments' in request.form
            backup_files = 'backup_files' in request.form
            backup_settings = 'backup_settings' in request.form
            
            # Create backup directory
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backups/{backup_name}_{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup database data
            cur = mysql.connection.cursor()
            
            if backup_users:
                cur.execute("SELECT * FROM user")
                users = cur.fetchall()
                with open(f"{backup_dir}/users.sql", "w", encoding="utf-8") as f:
                    f.write("-- Users Backup\n")
                    for user in users:
                        f.write(f"INSERT INTO user VALUES {user};\n")
            
            if backup_documents:
                cur.execute("SELECT * FROM document")
                documents = cur.fetchall()
                with open(f"{backup_dir}/documents.sql", "w", encoding="utf-8") as f:
                    f.write("-- Documents Backup\n")
                    for doc in documents:
                        f.write(f"INSERT INTO document VALUES {doc};\n")
            
            if backup_departments:
                cur.execute("SELECT * FROM section")
                sections = cur.fetchall()
                with open(f"{backup_dir}/sections.sql", "w", encoding="utf-8") as f:
                    f.write("-- Sections Backup\n")
                    for section in sections:
                        f.write(f"INSERT INTO section VALUES {section};\n")
            
            cur.close()
            
            # Backup uploaded files
            if backup_files:
                import shutil
                files_dir = f"{backup_dir}/files"
                os.makedirs(files_dir, exist_ok=True)
                if os.path.exists("static/uploads"):
                    shutil.copytree("static/uploads", files_dir, dirs_exist_ok=True)
            
            # Create backup metadata
            backup_info = {
                'backup_name': backup_name,
                'backup_type': backup_type,
                'compression': compression,
                'encryption': encryption,
                'schedule_type': schedule_type,
                'backup_time': backup_time,
                'retention_days': retention_days,
                'max_backups': max_backups,
                'backup_notes': backup_notes,
                'created_by': session['user_id'],
                'created_at': timestamp,
                'data_types': {
                    'users': backup_users,
                    'documents': backup_documents,
                    'departments': backup_departments,
                    'files': backup_files,
                    'settings': backup_settings
                }
            }
            
            import json
            with open(f"{backup_dir}/backup_info.json", "w", encoding="utf-8") as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            # Create backup summary
            with open(f"{backup_dir}/backup_summary.txt", "w", encoding="utf-8") as f:
                f.write(f"Backup Summary\n")
                f.write(f"==============\n")
                f.write(f"Name: {backup_name}\n")
                f.write(f"Type: {backup_type}\n")
                f.write(f"Created: {timestamp}\n")
                f.write(f"Created By: {session['user_name']}\n")
                f.write(f"Compression: {compression}\n")
                f.write(f"Encryption: {encryption}\n")
                f.write(f"Schedule: {schedule_type}\n")
                f.write(f"Retention: {retention_days} days\n")
                f.write(f"Max Backups: {max_backups}\n")
                f.write(f"Notes: {backup_notes}\n")
                f.write(f"\nData Included:\n")
                f.write(f"- Users: {'Yes' if backup_users else 'No'}\n")
                f.write(f"- Documents: {'Yes' if backup_documents else 'No'}\n")
                f.write(f"- Departments: {'Yes' if backup_departments else 'No'}\n")
                f.write(f"- Files: {'Yes' if backup_files else 'No'}\n")
                f.write(f"- Settings: {'Yes' if backup_settings else 'No'}\n")
            
            flash(f"تم إنشاء النسخة الاحتياطية بنجاح! تم حفظها في: {backup_dir}", "success")
            return redirect(url_for('dashboard'))
                
        except Exception as e:
            flash(f"خطأ في إنشاء النسخة الاحتياطية: {str(e)}", "error")
            print(f"Backup Error: {e}")

    return render_template('create_backup.html')
