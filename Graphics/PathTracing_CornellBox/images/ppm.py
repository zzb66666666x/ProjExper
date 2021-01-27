from PIL import Image
img = Image.open('binary_784x784_spp1024_thread4.ppm')
img.save('png_784x784_spp1024_thread4.png')
