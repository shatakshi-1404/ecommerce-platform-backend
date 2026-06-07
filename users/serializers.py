from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'phone', 'address']

    def create(self, validated_data):
        # Use create_user so password gets hashed properly
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'buyer'),
            phone=validated_data.get('phone', ''),
            address=validated_data.get('address', ''),
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        data['user'] = user
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone', 'address', 'profile_picture']
        read_only_fields = ['role']  # role can't be changed after registration