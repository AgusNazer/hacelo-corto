import redis
import json
import os
import subprocess
import cv2
import time
from app.pipeline import process

"""
============================
    worker.py
============================
Este es el worker que se ejecuta en el contenedor "worker" y se encarga de:
- Escuchar trabajos de procesamiento de video enviados por la API a través de Redis.
- Llamar a pipeline.py para procesar videos.
TODO:
- Etc. (a definir)
- Enviar eventos de vuelta a la API para que esta actualice la base de datos.(!?)
- No tiene acceso directo a la base de datos, solo se comunica vía redis.(!?)
"""



def check_ffmpeg():
    """
    Verifica que FFmpeg esté instalado en el contenedor
    y accesible desde el PATH del sistema.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.split("\n")[0]
    except Exception as e:
        return f"FFmpeg error: {e}"



def check_opencv():
    """
    Verifica que OpenCV esté correctamente instalado
    e importable desde Python.
    """
    try:
        return f"OpenCV version {cv2.__version__}"
    except Exception as e:
        return f"OpenCV error: {e}"



def check_redis():
    """
    Verifica conexión con Redis usando la variable de entorno REDIS_HOST.
    """
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)
        r.ping()
        return "Redis connected"
    except Exception as e:
        return f"Redis error: {e}"



def check_dependencies():
    """
    Ejecuta todos los chequeos de entorno al iniciar el worker.
    Sirve para validar que el contenedor está correctamente armado.
    """
    status = {
    "redis": check_redis(),
    "opencv": check_opencv(),
    "ffmpeg": check_ffmpeg()
    }
    
    print("🔎 Environment check:")
    for k, v in status.items():
        print(f"{k}: {v}")



def publish_event(r, event_type, extra_data=None):
    """
    Publica un evento al canal 'video_events' para que la API lo reciba.

    :param r: cliente Redis
    :param event_type: tipo de evento (string)
    :param extra_data: diccionario opcional con más datos
    """
    event = {"event": event_type}
    if extra_data:
        event.update(extra_data)

    r.publish("video_events", json.dumps(event))
    print(f"📤 Evento enviado: {event}", flush=True)



def redis_listener():
    """
    Conecta a Redis y queda escuchando el canal 'video_jobs'
    donde la API enviará trabajos de procesamiento de video.

    Este worker NO actualiza la base de datos.
    Solo procesa y luego notifica eventos.
    """

    print("🔌 Connecting to Redis...", flush=True)
    r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)

    # --- Enviar solo 2 mensajes de estado ---
    publish_event(r, "WORKER_STARTED")
    time.sleep(1)
    publish_event(r, "WORKER_READY")

    # --- Escuchar trabajos ---
    pubsub = r.pubsub()
    pubsub.subscribe("video_jobs")

    print("🎧 Worker listening for video jobs...", flush=True)

    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                job = json.loads(message["data"])
                print(f"🎬 Job recibed: {job}", flush=True)

                # 👉 Aquí irá luego el procesamiento real de video, algo asi...
                """
                try:
                    procesar(job["video_path"], job["inicio"], job["fin"])
                except Exception as e:
                    print("ERROR:", e, flush=True)
                """

                # Simular fin de procesamiento
                time.sleep(2)

                publish_event(r, "VIDEO_PROCESSED", {"job_id": job.get("job_id")})

            except Exception as e:
                print(f"⚠️ Error on job: {e}", flush=True)



if __name__ == "__main__":
    print("\n--------------")
    print(" VIDEO WORKER")
    print("--------------")
    print("\n🚀 VIDEO WORKER STARTING...\n", flush=True)

    check_dependencies()
    
    # Este loop infinto por ahora lo sacamos! Luego desde ahi vamos a llamar a procesar video...
    #redis_listener()

    # Llama a procesar manual para probar pipeline.py
    VIDEO_PATH = "example.mp4" #poner un video de prueba en el directorio /worker
    INICIO = 0
    FIN = 20
    try:
        process(VIDEO_PATH, INICIO, FIN)
    except Exception as e:
        print("ERROR:", e, flush=True)