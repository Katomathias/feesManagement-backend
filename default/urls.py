from django.urls import path
from . import views
from knox import views as knox_views

urlpatterns=[
	path('', views.homepage, name="homepage"),
    path('user-profile/<slug:slug>', views.user_profile_detail, name="user_profile_name"),
    path('stat', views.stats_view, name="stats"),
    path('students', views.user_profiles, name="students_page"),
    path('student', views.add_student, name="add_student") ,
    path('pay', views.add_payment, name="add_pay"),
    path('student/<slug:slug>', views.delete_student, name="delele_student"), 
    path('payments', views.payments, name="payments_page"),
    path('payments/<slug:slug>', views.payments, name="payments_one_page"),
    path('payment-details/<slug:slug>', views.payment_detail, name="payment_detail_page"),
     path('register', views.register, name="register"),
    path('login/', views.login, name="login"),
    path('logout/', knox_views.LogoutView.as_view(), name="logout"),
    path('logout-all/', knox_views.LogoutAllView.as_view(),name="logout_all"),
    path('change-password', views.change_password, name="change-password"),
    path('password-reset', views.password_reset, name="password-reset"),
    path('password-reset/<slug:slug>', views.password_reset_done, name="password-reset-done"),
    path('chart1', views.get_item_count, name="chart11"),
    path('nationality_counts', views.get_nationality_counts, name='nationality_counts'),
    path('amount_by_levels', views.get_amount_by_levels, name='amount_by_levels'),
]