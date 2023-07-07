from rest_framework import serializers
from users.models import CustomUser


class UserDetailsSerializers(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields=('id','username','first_name','email','password')

    def create(self, validated_data):
        user = CustomUser(
            # email=validated_data['email'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
