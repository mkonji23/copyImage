import os
import shutil


def copy_images(file_names, source_dir, target_dir, log_callback):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        log_callback(f"📁 대상 폴더 생성: {target_dir}")

    for name in file_names:
        matched_file = next(
            (f for f in os.listdir(source_dir) if os.path.splitext(f)[0] == name), None
        )
        if matched_file:
            shutil.copy2(
                os.path.join(source_dir, matched_file),
                os.path.join(target_dir, matched_file),
            )
            log_callback(f"✅ 복사됨: {matched_file}")
        else:
            log_callback(f"⚠️ 없음: {name}.*")
    return target_dir
