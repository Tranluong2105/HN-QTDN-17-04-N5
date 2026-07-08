{
    'name': "tai_chinh_ke_toan",
    'summary': "Kế toán khấu hao tài sản",
    'description': "Quản lý hồ sơ khấu hao, lịch sử khấu hao, sổ cái kế toán và email cảnh báo.",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base', 'mail', 'quan_ly_tai_san'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/ho_so_khau_hao.xml',
        'views/lich_su_khau_hao.xml',
        'views/so_cai_ke_toan.xml',
        'views/menu.xml',
    ],
}
