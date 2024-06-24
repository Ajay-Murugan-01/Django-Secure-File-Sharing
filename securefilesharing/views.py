import os
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import File
from .serializers import FileSerializer
from django.core.files.storage import FileSystemStorage
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse, Http404
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils.http import urlencode
import mimetypes

# import models
from django.contrib.auth.models import User

# import serializer
from .serializers import SignupSerializer, LoginSerializer

class SignUpView(APIView):

    signup_serializer_class = SignupSerializer

    def post(self, request):

        signup_serializer = self.signup_serializer_class(data=request.data)
        signup_serializer.is_valid(raise_exception=True)
        user = signup_serializer.save()

        token = Token.objects.create(user=user)

        send_mail(
            'Verify your email',
            'Please verify your email.',
            'from@ajay.com',
            [user.email],
            fail_silently=False,
        )

        return Response({'encrypted_url': token.key})

class Loginview(APIView):
    login_serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.login_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.login()
        user = User.objects.get(id=user.id)

        # Check if a token already exists for this user
        token, created = Token.objects.get_or_create(user=user)

        # If the token was not created (i.e., it already exists), return the existing token
        if not created:
            return Response({'encrypted_url': token.key})

        return Response({'encrypted_url': token.key})
        
class UploadFileView(APIView):

    def post(self, request):
        try:
            file = request.FILES.get('file')
            token = request.data.get('token')

            token = Token.objects.get(key=token)
            # print("token:", token.user)

            if file.name.endswith(('.pptx', '.docx', '.xlsx')):
                # print("request:", request.user)
                fs = FileSystemStorage()
                filename = fs.save(file.name, file)
                uploaded_file = File.objects.create(file=filename, uploaded_by=token.user)
                uploaded_file.save()
                return Response({'message': 'File uploaded successfully'})
            return Response({'message': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        except Token.DoesNotExist:
            return Response({'message': 'Token Invalid'}, status=status.HTTP_404_NOT_FOUND)

class ClientUserListFilesView(APIView):
    def get(self, request):
        try:
            encrypted_code  = request.data.get("encrypted_url")

            token = Token.objects.get(key=encrypted_code)

            if encrypted_code:
                files = File.objects.all()
                serializer = FileSerializer(files, many=True)
                return Response(serializer.data)
        except Token.DoesNotExist:
            return Response({'message': 'Token Invalid'}, status=status.HTTP_404_NOT_FOUND)

class DownloadFileView(APIView):
    def get(self, request, pk):
        try:
            file = File.objects.get(pk=pk)
            file_path = file.file.path

            # Ensure the file exists
            if not os.path.exists(file_path):
                raise Http404("File does not exist")

            # Generate a signed URL with a timestamp
            signer = TimestampSigner()
            signed_value = signer.sign(file_path)
            signed_url = f"{settings.MEDIA_URL}{file.file.name}?{urlencode({'token': signed_value})}"

            return Response({'download_url': request.build_absolute_uri(signed_url)})

        except File.DoesNotExist:
            return Response({'message': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
        
def serve_protected_file(request):
    try:
        signer = TimestampSigner()
        signed_token = request.GET.get('token')
        user_token = request.GET.get('user')

        original_user_token = signer.unsign(user_token, max_age=settings.SIGNED_URL_EXPIRY.total_seconds())

        if str(request.user.pk) != original_user_token:
            raise Http404("Unauthorized access")

        original_file_path = signer.unsign(signed_token, max_age=settings.SIGNED_URL_EXPIRY.total_seconds())

        if not os.path.exists(original_file_path):
            raise Http404("File does not exist")

        file_mime_type, _ = mimetypes.guess_type(original_file_path)
        response = HttpResponse(open(original_file_path, 'rb'), content_type=file_mime_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(original_file_path)}"'
        return response

    except (BadSignature, SignatureExpired):
        raise Http404("Invalid or expired token")
