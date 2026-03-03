from PIL import Image, ImageDraw, ImageFilter
import os

LEBAR = 1200
TINGGI = 1800

os.makedirs("static/backgrounds", exist_ok=True)
os.makedirs("static/frames", exist_ok=True)


def buat_gradient(warna_atas, warna_bawah, nama_file):
    img = Image.new("RGB", (LEBAR, TINGGI))
    draw = ImageDraw.Draw(img)
    for y in range(TINGGI):
        ratio = y / TINGGI
        r = int(warna_atas[0] + (warna_bawah[0] - warna_atas[0]) * ratio)
        g = int(warna_atas[1] + (warna_bawah[1] - warna_atas[1]) * ratio)
        b = int(warna_atas[2] + (warna_bawah[2] - warna_atas[2]) * ratio)
        draw.line([(0, y), (LEBAR, y)], fill=(r, g, b))
    img.save(f"static/backgrounds/{nama_file}")
    print(f"Background {nama_file} selesai")


def buat_background_solid(warna, nama_file):
    img = Image.new("RGB", (LEBAR, TINGGI), warna)
    img.save(f"static/backgrounds/{nama_file}")
    print(f"Background {nama_file} selesai")


def buat_frame_hitam(nama_file):
    img = Image.new("RGBA", (LEBAR, TINGGI), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    tebal = 18
    draw.rectangle([0, 0, LEBAR-1, TINGGI-1], outline=(20, 20, 20, 255), width=tebal)
    draw.rectangle([tebal+8, tebal+8, LEBAR-tebal-9, TINGGI-tebal-9], outline=(20, 20, 20, 100), width=4)
    img.save(f"static/frames/{nama_file}")
    print(f"Frame {nama_file} selesai")


def buat_frame_merah_putih(nama_file):
    img = Image.new("RGBA", (LEBAR, TINGGI), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    tebal = 22
    draw.rectangle([0, 0, LEBAR-1, TINGGI//2], outline=(0, 0, 0, 0), width=0)

    for y in range(TINGGI // 2):
        alpha = 255
        draw.line([(0, y), (LEBAR, y)], fill=(200, 0, 0, alpha))
    for y in range(TINGGI // 2, TINGGI):
        draw.line([(0, y), (LEBAR, y)], fill=(240, 240, 240, 255))

    mask = Image.new("RGBA", (LEBAR, TINGGI), (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask)
    margin = tebal + 10
    mask_draw.rectangle([margin, margin, LEBAR-margin, TINGGI-margin], fill=(0, 0, 0, 255))

    hasil = Image.new("RGBA", (LEBAR, TINGGI), (0, 0, 0, 0))
    for y in range(TINGGI):
        for x in range(LEBAR):
            mx = mask.getpixel((x, y))[3]
            if mx == 0:
                hasil.putpixel((x, y), img.getpixel((x, y)))
            else:
                hasil.putpixel((x, y), (0, 0, 0, 0))

    draw2 = ImageDraw.Draw(hasil)
    draw2.rectangle([0, 0, LEBAR-1, TINGGI-1], outline=(180, 0, 0, 255), width=tebal)
    draw2.rectangle([tebal, tebal, LEBAR-tebal-1, TINGGI//2], outline=(255, 255, 255, 180), width=3)
    draw2.rectangle([tebal, TINGGI//2, LEBAR-tebal-1, TINGGI-tebal-1], outline=(200, 0, 0, 180), width=3)

    hasil.save(f"static/frames/{nama_file}")
    print(f"Frame {nama_file} selesai")


def buat_frame_gold(nama_file):
    img = Image.new("RGBA", (LEBAR, TINGGI), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    tebal_luar = 20
    tebal_dalam = 4
    gap = 10

    draw.rectangle([0, 0, LEBAR-1, TINGGI-1], outline=(184, 142, 40, 255), width=tebal_luar)
    draw.rectangle(
        [tebal_luar+gap, tebal_luar+gap, LEBAR-tebal_luar-gap-1, TINGGI-tebal_luar-gap-1],
        outline=(212, 175, 55, 255), width=tebal_dalam
    )
    draw.rectangle(
        [tebal_luar+gap+6, tebal_luar+gap+6, LEBAR-tebal_luar-gap-7, TINGGI-tebal_luar-gap-7],
        outline=(184, 142, 40, 180), width=2
    )

    ukuran_sudut = 30
    warna_sudut = (220, 190, 80, 255)
    posisi_sudut = [
        (0, 0),
        (LEBAR - ukuran_sudut, 0),
        (0, TINGGI - ukuran_sudut),
        (LEBAR - ukuran_sudut, TINGGI - ukuran_sudut),
    ]
    for px, py in posisi_sudut:
        draw.rectangle([px, py, px+ukuran_sudut, py+ukuran_sudut], outline=warna_sudut, width=4)

    img.save(f"static/frames/{nama_file}")
    print(f"Frame {nama_file} selesai")


print("Membuat background...")
buat_gradient((30, 80, 200), (10, 40, 120), "biru_studio.jpg")
buat_gradient((90, 90, 90), (40, 40, 40), "abu_studio.jpg")
buat_background_solid((255, 255, 255), "putih.jpg")
buat_background_solid((180, 20, 20), "merah.jpg")
buat_gradient((120, 190, 120), (60, 140, 60), "hijau.jpg")

print("Membuat frame...")
buat_frame_hitam("frame_hitam.png")
buat_frame_merah_putih("frame_merah_putih.png")
buat_frame_gold("frame_gold.png")

print("Semua asset selesai dibuat!")