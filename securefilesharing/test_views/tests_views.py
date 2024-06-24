import os
from django.test import TestCase, RequestFactory
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from securefilesharing.models import File
from securefilesharing.views import SignUpView, Loginview, UploadFileView, ClientUserListFilesView, DownloadFileView, serve_protected_file
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils.http import urlencode
import mimetypes
from rest_framework.response import Response
from securefilesharing.serializers import FileSerializer, SignupSerializer, LoginSerializer
from django.core.mail import send_mail

class SignUpViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_signup(self):
        url = '/api/signup/'  
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('encrypted_url', response.data)
        self.assertTrue(User.objects.filter(username='testuser').exists())

class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')

    def test_login(self):
        url = '/api/login/'  
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('encrypted_url', response.data)

class UploadFileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.token = Token.objects.create(user=self.user).key

    def test_upload_valid_file(self):
        url = '/api/upload/'  
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile('testfile.docx', file_content, content_type='application/msword')

        data = {
            'file': uploaded_file,
            'token': self.token
        }

        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'File uploaded successfully')

class ClientUserListFilesViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.token = Token.objects.create(user=self.user).key

    def test_list_files(self):
        url = '/api/list_files/'  
        response = self.client.get(url, {'encrypted_url': self.token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class DownloadFileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.token = Token.objects.create(user=self.user).key
        self.file = File.objects.create(file='testfile.docx', uploaded_by=self.user)

    def test_download_file(self):
        url = f'/api/download/{self.file.pk}/'  
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)

class ServeProtectedFileTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.token = TimestampSigner().sign(str(self.user.pk))

    def test_serve_protected_file(self):
        request = self.factory.get('/api/serve_protected_file/', {'token': self.token, 'user': self.token})
        request.user = self.user

        response = serve_protected_file(request)
        self.assertEqual(response.status_code, 200)

    def test_serve_protected_file_expired_token(self):
        expired_token = TimestampSigner().sign(str(self.user.pk), max_age=-1)  # Expired token
        request = self.factory.get('/api/serve_protected_file/', {'token': expired_token, 'user': expired_token})
        request.user = self.user

        with self.assertRaises(Http404):
            serve_protected_file(request)


