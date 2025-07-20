import os, tempfile, ffmpeg
from minio import Minio
from flask import current_app, jsonify
from datetime import timedelta
from data.orm import SyncORM

def get_s3_client():
    client = Minio(
        current_app.config['AWS_S3_ENDPOINT_URL'],
        access_key=current_app.config['AWS_ACCESS_KEY_ID'],
        secret_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        secure=False
    )
    return client

def upload_video(file_obj, filename, uid):
    s3 = get_s3_client()

    # Сохраняем оригинал во временный файл
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = os.path.join(temp_dir, filename)
        file_obj.save(input_path)

        # Путь для mp4-файла
        mp4_filename = f"{uid}.mp4"
        output_path_mp4 = os.path.join(temp_dir, mp4_filename)

        # Путь для jpeg-файла
        jpeg_filename = f"{uid}.jpeg"
        output_path_jpeg = os.path.join(temp_dir, jpeg_filename)

        # Конвертация через ffmpeg
        try:
            (
                ffmpeg
                .input(input_path)
                .output(output_path_mp4,
                        vcodec='libx264',
                        acodec='aac'
                        )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            (
                ffmpeg
                .input(input_path, ss='00:00:03')
                .output(output_path_jpeg, vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            raise RuntimeError("Ошибка ffmpeg:\n" + e.stderr.decode())

        # Загрузка в MinIO
        s3.fput_object(
            bucket_name=current_app.config['AWS_BUCKET_NAME_VIDEOS'],
            object_name=mp4_filename,
            file_path=output_path_mp4,
            content_type='video/mp4'
        )
        s3.fput_object(
            bucket_name=current_app.config['AWS_BUCKET_NAME_THUMBNAILS'],
            object_name=jpeg_filename,
            file_path=output_path_jpeg,
            content_type="image/jpeg"
        )
    
def get_url_video(uid):
    s3 = get_s3_client()
    presigned_url = s3.presigned_get_object(
        bucket_name="videos", 
        object_name=f"{uid}.mp4", 
        expires=timedelta(hours=1)
        )
    return presigned_url

def get_url_thumb(uid):
    s3 = get_s3_client()
    presigned_url = s3.presigned_get_object(
        bucket_name="thumbnails", 
        object_name=f"{uid}.jpeg", 
        expires=timedelta(hours=1)
        )
    return presigned_url

def delete_video(uid):
    SyncORM.delete_meta_video(uid)
    
    s3 = get_s3_client()
    s3.remove_object(
        bucket_name=current_app.config['AWS_BUCKET_NAME_VIDEOS'], 
        object_name=f"{uid}.mp4"
    )
    s3.remove_object(
        bucket_name=current_app.config['AWS_BUCKET_NAME_THUMBNAILS'], 
        object_name=f"{uid}.jpeg"
    )