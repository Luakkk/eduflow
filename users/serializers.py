from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ("username","email","password","role")

    def validate_email(self, value):
        validate_email(value); return value

    def create(self, data):
        pwd = data.pop("password")
        user = User(**data)
        validate_password(pwd, user)
        user.set_password(pwd)
        user.save()
        return user

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id","username","email","role","date_joined")
        read_only_fields = fields
