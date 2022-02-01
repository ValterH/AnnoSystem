import os
import re
import sys
import json
import copy
import argparse
from functools import partial


import numpy as np


from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
	QAction, QMainWindow, QLabel, 
	QVBoxLayout, QRadioButton)
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt


import styles


ROOT_DIR = 'data/'
ANNO_DIR = 'data/annos/'
if not os.path.exists(ANNO_DIR):
	os.makedirs(ANNO_DIR)
part_names = ["nose", "right eye", "right ear", "right shoulder",
			  "right elbow", "right wrist", "right hip", "right knee",
			  "right ankle", "left eye", "left ear", "left shoulder",
			  "left elbow", "left wrist", "left hip", "left knee", "left ankle"]

class Annos():
	def __init__(self):
		self.init()

	def init(self):
		self.imagepath = None
		self.scaleratio = 1.0
		self.keypoints = []
		self.cur_keypoint = np.zeros((17,3), dtype = np.float32)
		self.cur_part_id = 0
		self.cur_vis = True

	def new_item(self):
		self.keypoints.append(copy.deepcopy(self.cur_keypoint.reshape(-1).tolist()))
		self.cur_keypoint = np.zeros((17,3), dtype = np.float32)
		self.cur_part_id = 0
		self.cur_vis = True

	def savejson(self):
		if self.imagepath:
			if np.sum(self.cur_keypoint) > 0:
				self.new_item()
			if len(self.keypoints) > 0:
				res = {'imagepath': self.imagepath, 
					   'scaleratio': self.scaleratio, 
					   'keypoints':self.keypoints}
				#remove first folder
				savepath = re.sub(r"[a-z]+\/",'',self.imagepath)
				#remove third folder
				savepath = re.sub(r"\/",'',savepath) 
				savepath = ANNO_DIR + savepath + '_annos.json'
				with open(savepath, 'w') as f:
					json.dump(res, f)

	def print(self, log):
		print ('-------------- < %s > ------------'%log)
		print ('imagepath:', self.imagepath)
		print ('scaleratio:', self.scaleratio)
		print ('keypoints:', self.keypoints)
		print ('cur_keypoint:', self.cur_keypoint)
		print ('cur_part:', part_names[self.cur_part_id])
		print ('cur_vis:', self.cur_vis)

CurrentAnnos = Annos()

class MyQLabel(QLabel):

	def __init__(self, parent):
		super().__init__(parent)
		self.parent = parent
		self.label_maxw = 1200.0
		self.label_maxh = 700.0
		self.setGeometry(50, 50, int(self.label_maxw), int(self.label_maxh)) 

		self.pen = QPen()
		self.pen.setWidth(5)
		self.pen.setBrush(Qt.red)

		self.pos = None
		self.png = None
	
	def update(self):
		super().update()

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		if self.png:
			qp.drawPixmap(0,0, self.png)
		for i, keypoints in enumerate(CurrentAnnos.cur_keypoint):
			if keypoints[0] > 0 and keypoints[1] > 0:
				self.pen.setBrush(styles.colors[i])
				x = int(keypoints[0])
				y = int(keypoints[1])
				if keypoints[2] == 1:
					self.pen.setWidth(5)
					qp.setPen(self.pen)
					qp.drawPoint(x, y)
				else:
					self.pen.setWidth(2)
					qp.setPen(self.pen)
					qp.drawEllipse(x-2, y-2, 5,5)
		qp.end()

	def mousePressEvent(self, e):
		self.pos = e.pos()
		print ('PRESS: %d,%d'%(self.pos.x(), self.pos.y()))
		self.update() 

		global CurrentAnnos
		if CurrentAnnos.imagepath:
			CurrentAnnos.cur_keypoint[CurrentAnnos.cur_part_id, 0] = self.pos.x()
			CurrentAnnos.cur_keypoint[CurrentAnnos.cur_part_id, 1] = self.pos.y()
			if CurrentAnnos.cur_vis == True:
				CurrentAnnos.cur_keypoint[CurrentAnnos.cur_part_id, 2] = 1
			elif CurrentAnnos.cur_vis == False:
				CurrentAnnos.cur_keypoint[CurrentAnnos.cur_part_id, 2] = 2
			CurrentAnnos.print('mousePressEvent')
		#self.parent.nextPart()

	def loadimg(self, filename):

		self.pos = None
		png = QPixmap(filename)
		ratio = min( self.label_maxw / png.width(), self.label_maxh / png.height())
		self.png = png.scaled(png.width()*ratio, png.height()*ratio)
		self.update() 

		global CurrentAnnos
		CurrentAnnos.init()
		CurrentAnnos.imagepath = filename
		CurrentAnnos.scaleratio = ratio
		CurrentAnnos.print('loadimg')

class ControlWindow(QMainWindow):
	def __init__(self, dir= '00'):
		super(ControlWindow, self).__init__()
		self.setGeometry(50, 50, 1400, 800)
		self.setWindowTitle(dir)

		self.nextImageAction = QAction("&NextImage", self)
		self.nextImageAction.setShortcut("Q")
		self.nextImageAction.triggered.connect(partial(self.nextImage, +1))
		self.preImageAction = QAction("&PreImage", self)
		self.preImageAction.setShortcut("A")
		self.preImageAction.triggered.connect(partial(self.nextImage, -1))

		self.nextItemAction = QAction("&NextItem", self)
		self.nextItemAction.setShortcut("D")
		self.nextItemAction.triggered.connect(self.nextItem)
		self.nextPartAction = QAction("&NextPart", self)
		self.nextPartAction.setShortcut("W")
		self.nextPartAction.triggered.connect(self.nextPart)
		self.lastPartAction = QAction("&LastPart", self)
		self.lastPartAction.setShortcut("R")
		self.lastPartAction.triggered.connect(self.lastPart)
		self.changeVisAction = QAction("&ChangeVisState", self)
		self.changeVisAction.setShortcut("E")
		self.changeVisAction.triggered.connect(self.changeVisState)

		self.mainMenu = self.menuBar()
		self.mainMenu.addAction(self.nextImageAction)
		self.mainMenu.addAction(self.preImageAction)
		self.mainMenu.addAction(self.nextItemAction)
		self.mainMenu.addAction(self.changeVisAction)
		self.mainMenu.addAction(self.nextPartAction)
		self.mainMenu.addAction(self.lastPartAction)

		self.currentID = -1
		self.dir = ROOT_DIR+dir +'/images'
		self.imagelist = os.listdir(self.dir)
		self.imagelist = [item for item in self.imagelist if item[-4:]=='.jpg']
		self.imagelist.sort(key=lambda x:int(x[7:4:-1][::-1]))

		self.qlabel = MyQLabel(self)

		body_part_box = QWidget(self)
		body_part_box_layout = QVBoxLayout()
		self.buttonlist = []
		for i in range(17):
			button = QRadioButton(part_names[i])
			button.clicked.connect(partial(self.changePart, i))
			self.buttonlist.append(button)
			body_part_box_layout.addWidget(button)

		self.buttonlist[0].setChecked(True)
		self.buttonlist[0].setStyleSheet(styles.backgrounds[CurrentAnnos.cur_part_id])
		
		body_part_box.setLayout(body_part_box_layout)
		body_part_box.setGeometry(0, 50, 100, 600) 
		body_part_box.setStyleSheet(styles.BLANK)

		self.hintbox = QLabel(self)
		self.hintbox.setGeometry(0, 0, 1000, 75)
		self.hintbox.setText('The next/previous picture: Q/A\t'     \
							 'The next person in this picture: D\t' \
							 'The next/previous part: W/R\t '       \
							 'Change visibility: E') 
		self.hintbox.setFont(QFont('Times', 10))


	def nextImage(self, direction):
		global CurrentAnnos
		CurrentAnnos.savejson()
		self.currentID += direction
		self.currentID = min(max(self.currentID, 0), len(self.imagelist)-1)
		self.currentPath = '%s/%s'%(self.dir, self.imagelist[self.currentID])
		self.qlabel.loadimg(self.currentPath)
		self.setWindowTitle(self.currentPath)
		
		self.buttonlist[CurrentAnnos.cur_part_id].setChecked(True)
		for bt in self.buttonlist:
			bt.setStyleSheet(styles.NO_COLOR)
		self.buttonlist[CurrentAnnos.cur_part_id].setStyleSheet(
			styles.backgrounds[CurrentAnnos.cur_part_id])
		CurrentAnnos.print('nextImage')

	def nextItem(self):
		global CurrentAnnos
		CurrentAnnos.new_item()
		self.buttonlist[CurrentAnnos.cur_part_id].setChecked(True)
		for bt in self.buttonlist:
			bt.setStyleSheet(styles.NO_COLOR)
		self.buttonlist[CurrentAnnos.cur_part_id].setStyleSheet(
			styles.backgrounds[CurrentAnnos.cur_part_id])
		CurrentAnnos.print('nextItem')

	def nextPart(self):
		global CurrentAnnos
		CurrentAnnos.cur_part_id += 1
		CurrentAnnos.cur_part_id = CurrentAnnos.cur_part_id % 17
		CurrentAnnos.cur_vis = True
		self.buttonlist[CurrentAnnos.cur_part_id].setChecked(True)
		self.buttonlist[CurrentAnnos.cur_part_id].setStyleSheet(
			styles.backgrounds[CurrentAnnos.cur_part_id])
		
		CurrentAnnos.print('nextPart')
	
	def lastPart(self):
		global CurrentAnnos
		CurrentAnnos.cur_part_id -= 1
		CurrentAnnos.cur_part_id = CurrentAnnos.cur_part_id % 17
		CurrentAnnos.cur_vis = True
		self.buttonlist[CurrentAnnos.cur_part_id].setChecked(True)
		self.buttonlist[CurrentAnnos.cur_part_id].setStyleSheet(
			styles.backgrounds[CurrentAnnos.cur_part_id])
		
		CurrentAnnos.print('lastPart')

	def changePart(self, id):
		global CurrentAnnos
		CurrentAnnos.cur_part_id = id
		CurrentAnnos.cur_vis = True
		self.buttonlist[CurrentAnnos.cur_part_id].setChecked(True)
		self.buttonlist[CurrentAnnos.cur_part_id].setStyleSheet(
			styles.backgrounds[CurrentAnnos.cur_part_id])
		CurrentAnnos.print('changePart')

	def changeVisState(self):
		global CurrentAnnos
		CurrentAnnos.cur_vis = bool((CurrentAnnos.cur_vis + 1) % 2)
		CurrentAnnos.print('changeVisState')


if __name__ == '__main__':
	a = argparse.ArgumentParser()
	a.add_argument("--dir", help="image subfolder", default='00')
	args = a.parse_args()
	app = QApplication(sys.argv)
	window = ControlWindow(dir=args.dir)
	window.show()
	sys.exit(app.exec_())


