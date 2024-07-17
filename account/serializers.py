from rest_framework import serializers
from .models import CustomUser , Product, Order
import base64
from django.core.files.base import ContentFile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'password']
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'phone_number': {'required': True, 'allow_blank': False},
            'password': {'required': True, 'allow_blank': False, 'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = self.Meta.model(**validated_data)
        if password is not None:
            user.set_password(password)
        user.save()
        return user


class ProductSerializer(serializers.ModelSerializer):
    image_base64 = serializers.CharField(write_only=True, required=False)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = self.encode_image(instance.image)
        return representation

    def create(self, validated_data):
        image_data = validated_data.pop('image_base64', None)
        instance = self.Meta.model(**validated_data)
        
        if image_data:
            
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            decoded_image = base64.b64decode(imgstr)
            filename = f"product_image.{ext}"
            instance.image.save(filename, ContentFile(decoded_image), save=False)

        instance.save()
        return instance

    def encode_image(self, image):
        with image.open(mode='rb') as img_file:
            encoded_image_data = base64.b64encode(img_file.read()).decode('utf-8')
            return f"data:image/{image.name.split('.')[-1]};base64,{encoded_image_data}"

    class Meta:
        model = Product
        fields = '__all__'
        extra_kwargs = {
            'image': {'required': True}}

class OrderSerializer(serializers.ModelSerializer):
    
    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    
    class Meta:
        model = Order
        fields = ['user_id', 'product_ids']
        
    def validate_product_ids(self, product_ids):
        
        products = []
        for product_id in product_ids:
            try:
                product = Product.objects.get(id=product_id)
                products.append(product)
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with id '{product_id}' does not exist.")
        
        return products

    def create(self, validated_data):
        products = validated_data.pop('product_ids')
        order = Order.objects.create(user_id=validated_data['user_id'])
        order.products.set(products)
        return order    
        
        