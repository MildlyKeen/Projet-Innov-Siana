import os

# 📁 Dossier contenant les images
folder_path = "trains_images"

# Extensions autorisées
image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

# Récupération et tri des fichiers image
images = sorted(
    f for f in os.listdir(folder_path)
    if os.path.splitext(f)[1].lower() in image_extensions
)

# Renommage
for i, filename in enumerate(images, start=1):
    old_path = os.path.join(folder_path, filename)
    extension = os.path.splitext(filename)[1]
    new_name = f"trains_{i}{extension}"
    new_path = os.path.join(folder_path, new_name)

    if os.path.exists(new_path):
        raise FileExistsError(f"{new_name} existe déjà. Renommage annulé.")

    os.rename(old_path, new_path)

print("✅ Renommage terminé.")
