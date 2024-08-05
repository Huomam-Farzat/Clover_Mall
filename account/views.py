import jwt
import json
import base64
import logging
import datetime
import traceback

from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status

from .models import CustomUser , Product , Order
from .serializers import UserSerializer , ProductSerializer , OrderSerializer
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
def inputData(request):
    try:
        data = request.data
        phone_number = data.get('phone_number')
        us = CustomUser.objects.all()

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            return JsonResponse({"data": "Number already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if len(phone_number) != 10:
            return JsonResponse({"data": "Your number is not 10 digits"}, status=status.HTTP_400_BAD_REQUEST)

        if not phone_number.startswith("09"):
            return JsonResponse({"data": "Your number doesn't begin with '09'!"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(data.get('password'))
            user.save()
            token = RefreshToken.for_user(user)
            tokens = {
                "refresh": str(token),
                "access": str(token.access_token),
            }
            return JsonResponse({"data": "saved", "token": tokens}, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except json.JSONDecodeError:
        return JsonResponse({"data": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return JsonResponse({"data": "Something went wrong with your information, please make sure you are entering it correctly"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def getuser(request):
    token = request.COOKIES.get('jwt')

    if not token:
        raise AuthenticationFailed("Unauthenticated!", status=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Unauthenticated!', status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Invalid token!', status=status.HTTP_401_UNAUTHORIZED)

    user = CustomUser.objects.filter(id=payload['id']).first()
    if not user:
        raise AuthenticationFailed('User not found!', status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def login(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    user = CustomUser.objects.filter(phone_number=phone_number).first()

    if user is None:
        raise AuthenticationFailed('User not found!', status=status.HTTP_401_UNAUTHORIZED)
    if not user.check_password(password):
        raise AuthenticationFailed('Incorrect password!', status=status.HTTP_401_UNAUTHORIZED)

    payload = {
        'id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    response = Response()
    response.set_cookie(key='jwt', value=token, httponly=True, samesite='Strict')
    response.data = {
        'detail': 'Login successful',
        'jwt': token,
        "status": status.HTTP_202_ACCEPTED
    }
    return response


@api_view(['POST'])
def register(request):
    try:
        data = request.data
        phone_number = data.get('phone_number')
        username = data.get('username')

        phonenumber = CustomUser.objects.filter(phone_number=phone_number)
        us = CustomUser.objects.filter(username=username)

        if len(phone_number) != 10:
            return Response({"data": "Your number is not 10 digits"}, status=status.HTTP_400_BAD_REQUEST)

        elif not phone_number.startswith("09"):
            return Response({"data": "Your number doesn't begin with '09'!"}, status=status.HTTP_400_BAD_REQUEST)

        elif phonenumber.exists():
            return Response({"data": "Number already exists"}, status=status.HTTP_400_BAD_REQUEST)

        elif us.exists():
            return Response({"data": "username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save()
            user.set_password(data.get('password'))
            user.save()

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=180),
            'iat': datetime.datetime.utcnow()
        }
        print(payload)
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        response = Response()
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token,
            "status": status.HTTP_201_CREATED,
        }
        return response

    except Exception as e:
        print(e)
        return Response({"data": "something wrong!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def test_token(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = CustomUser.objects.get(phone_number=request.data['phone'])
        user.set_password(request.data['password'])
        user.save()
        token = RefreshToken.for_user(user)
        return Response({"token": str(token.access_token), "user": serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request):
    response = Response()
    response.delete_cookie('jwt')
    response.data = {
        'message': 'success'
    }
    return response


logger = logging.getLogger(__name__)

# Product Views
@api_view(['GET'])
def get_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_products_by_category(request, category_name):
    try:
        category_choices = {
            "foodandbeverages": "Food and Beverages",
            "householdsupplies": "Household Supplies",
            "healthbeauty": "Health Beauty",
            "clothingaccessories": "Clothing Accessories",
            "electronicsappliances": "Electronics Appliances",
            "savorydelight": "Savory Delight",
            "urbanbite": "Urban Bite",
            "trendsetters": "Trend Setters",
            "gourmetcorner": "Gourmet Corner",
            "techworld": "Tech World",
        }

        if category_name not in category_choices:
            return Response({"detail": "Invalid category"}, status=status.HTTP_400_BAD_REQUEST)

        products = Product.objects.filter(category=category_choices[category_name])
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return Response({"detail": "Error fetching products"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def enter_product(request):
    try:
        data = request.data.copy()

        # Handle image file upload
        if 'image' in request.FILES:
            image = request.FILES['image']

            # base64 encoding
            encoded_image = base64.b64encode(image.read()).decode('utf-8')
            data['image_base64'] = f"data:image/{image.name.split('.')[-1]};base64,{encoded_image}"

        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Order Views
@api_view(['POST'])
def create_order(request):
    try:
        token = request.data.get('jwt')
        if not token:
            return Response({"detail": "JWT token not provided in request body."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('id')
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user_id:
            return Response({"detail": "Invalid token format - no user ID found."}, status=status.HTTP_401_UNAUTHORIZED)

        user = get_object_or_404(CustomUser, id=user_id)

        product_data = request.data.get('products')
        if not product_data:
            return Response({"detail": "Product data not provided."}, status=status.HTTP_400_BAD_REQUEST)

        product_ids = []
        for product in product_data:
            product_id = product.get('id')
            if not product_id:
                return Response({"detail": "Product ID not provided."}, status=status.HTTP_400_BAD_REQUEST)
            product_ids.append(product_id)

        data = {
            'user_id': user.id,
            'product_ids': product_ids
        }

        serializer = OrderSerializer(data=data)
        if serializer.is_valid():
            order = serializer.save()

            # Prepare response data including product details
            product_details = []
            for product in order.products.all():
                product_details.append({
                    'id': product.id,
                    'name': product.name,
                    'category': product.category
                })

            response_data = {
                "order_id": order.id,
                "user_id": order.user_id,
                "products": product_details,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_orders(request):
    try:
        orders = Order.objects.all()
        order_data = []

        for order in orders:
            order_info = {
                'order_id': order.id,
                'user_id': order.user_id,
                'products': [
                    {
                        'id': product.id,
                        'name': product.name,
                        'category': product.category,
                    } for product in order.products.all()
                ]
            }
            order_data.append(order_info)

        return Response(order_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_user_orders(request):
    try:
        token = request.data.get('jwt')
        if not token:
            return Response({"detail": "JWT token not provided in request body."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('id')
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user_id:
            return Response({"detail": "Invalid token format - no user ID found."}, status=status.HTTP_401_UNAUTHORIZED)

        user = get_object_or_404(CustomUser, id=user_id)

        orders = Order.objects.filter(user_id=user.id)
        order_data = []

        for order in orders:
            order_info = {
                'order_id': order.id,
                'products': [
                    {
                        'id': product.id,
                        'name': product.name,
                        'category': product.category
                    }
                    for product in order.products.all()
                ]
            }
            order_data.append(order_info)

        return Response(order_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"detail": "Internal server error: {}".format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_orders_by_main_categories(request):
    try:
        main_categories = [
            "Food and Beverages",
            "Household Supplies",
            "Health Beauty",
            "Clothing Accessories",
            "Electronics Appliances"
        ]

        orders = Order.objects.filter(products__category__in=main_categories).distinct()
        order_data = []

        for order in orders:
            order_info = {
                'order_id': order.id,
                'products': [
                    {
                        'id': product.id,
                        'name': product.name,
                        'category': product.category
                    }
                    for product in order.products.filter(category__in=main_categories)
                ]
            }
            order_data.append(order_info)

        return Response(order_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_orders_by_store(request, store_name):
    try:
        category_choices = {
            "savorydelight": "Savory Delight",
            "urbanbite": "Urban Bite",
            "trendsetters": "Trend Setters",
            "gourmetcorner": "Gourmet Corner",
            "techworld": "Tech World",
        }

        if store_name.lower() not in category_choices:
            return Response({"detail": f"Store '{store_name}' does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        orders = Order.objects.filter(products__category=category_choices[store_name.lower()]).distinct()

        order_data = []

        for order in orders:
            order_info = {
                'order_id': order.id,
                'user_id': order.user_id,
                'products': [
                    {
                        'id': product.id,
                        'name': product.name,
                        'category': product.category
                    }
                    for product in order.products.filter(category=category_choices[store_name.lower()])
                ]
            }
            order_data.append(order_info)

        return Response(order_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error fetching orders by store: {e}")
        return Response({"detail": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def newproducts(request):
    if request.method == 'GET':
        try:
            pr = Product.objects.filter(date=timezone.now().date()).order_by('-date')[:5]
            serializer = ProductSerializer(pr, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching new products: {e}")
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@csrf_exempt
def bestrate(request):
    if request.method == 'GET':
        try:
            rate = Product.objects.order_by('-rating')[:5]
            serializer = ProductSerializer(rate, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching best rated products: {e}")
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


from decimal import Decimal
from bson.decimal128 import Decimal128

@api_view(['GET'])
def rateplus(request):
    try:
        product_id = request.query_params.get('product_id')
        category = request.query_params.get('category')

        if not product_id or not category:
            return Response({"data": "error", "message": "Missing product_id or category"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, category=category)
        except Product.DoesNotExist:
            return Response({"data": "error", "message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Convert Decimal128 to Decimal if needed
        if isinstance(product.price, Decimal128):
            try:
                product.price = Decimal(product.price.to_decimal())
            except Exception as e:
                return Response({"data": "error", "message": f"Error converting price: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        product.rating = (product.rating or 0) + 1

        serializer = ProductSerializer(product, data={'rating': product.rating}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": "success", "rating": serializer.data['rating']}, status=status.HTTP_200_OK)
        else:
            return Response({"data": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Exception details: {traceback.format_exc()}")
        return Response({"data": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def rateminus(request):
    try:
        product_id = request.query_params.get('product_id')
        category = request.query_params.get('category')

        if not product_id or not category:
            return Response({"data": "error", "message": "Missing product_id or category"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, category=category)
        except Product.DoesNotExist:
            return Response({"data": "error", "message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Convert Decimal128 to Decimal if needed
        if isinstance(product.price, Decimal128):
            try:
                product.price = Decimal(product.price.to_decimal())
            except Exception as e:
                return Response({"data": "error", "message": f"Error converting price: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        product.rating = (product.rating or 0) - 1

        serializer = ProductSerializer(product, data={'rating': product.rating}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": "success", "rating": serializer.data['rating']}, status=status.HTTP_200_OK)
        else:
            return Response({"data": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Exception details: {traceback.format_exc()}")
        return Response({"data": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
