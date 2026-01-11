The backend will be run on uvicron and frontend from either live server or live  preview extension
The minio storage will be made using docker 

# minio set-up after docker
docker run -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -e "MINIO_API_CORS_ALLOW_ORIGIN=*" \
  minio/minio server /data --console-address ":9001"
  
