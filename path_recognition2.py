"""Test the image tracer."""
import cv2
import glob
from matplotlib import pyplot as plt

image = cv2.imread("./images/sample_01.jpg")
height, width = image.shape[:2]

imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

scale_percent = 100  # percent of original size
width = int(image.shape[1] * scale_percent / 100)
height = int(image.shape[0] * scale_percent / 100)
dim = (width, height)

# resize image
imgray = cv2.resize(imgray, dim, interpolation=cv2.INTER_AREA)

# plt.imshow(imgray, cmap='gray')
# plt.show()

# cv2.imshow('image', imgray)
# cv2.waitKey(0)

ret, thresh = cv2.threshold(imgray, 200, 255, cv2.THRESH_BINARY)

# gray = cv2.cvtColor(thresh, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(thresh, (3, 3), 0)
b = blurred.astype(float) / 255
b = b.astype(int) * 255
plt.imshow(b, cmap='gray')
plt.show()
# edged = cv2.Canny(blurred, 180, 200)
# print(edged)
# plt.imshow(edged, cmap='gray')
# plt.show()

# output = cv2.bitwise_not(b)

# plt.imshow(output, cmap='gray')
# plt.show()

cv2.imwrite('./images/sample_03.jpg', b)

# contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_TC89_L1)
#
# # c = max(contours, key=cv2.contourArea) #max contour
# f = open('sample.svg', 'w+')
# f.write('<svg width="'+str(width)+'" height="'+str(height)+'" xmlns="http://www.w3.org/2000/svg">')
#
# # for i in range(len(c)):
# #     #print(c[i][0])
# #     x, y = c[i][0]
# #     print(x)
# #     f.write(str(x)+  ' ' + str(y)+' ')
#
# for c in contours:
#     f.write('<path d="M')
#     for i in range(len(c)):
#         x, y = c[i][0]
#         f.write(f"{x} {y} ")
#     f.write('" style="stroke:pink"/>')
# f.write("</svg>")
#
# # f.write('"/>')
# # f.write('</svg>')
# f.close()