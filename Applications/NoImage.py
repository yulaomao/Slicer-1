import os
import sys
import vtk, qt, slicer
from qt import Signal
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import numpy as np
import math
import time
import threading
import socket
from PySide2.QtWidgets import QVBoxLayout
import shiboken2
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
try:
  slicer.util.pip_install("pyserial")
  import serial
except:
  pass

# from VRControl import VRControl

sys.path.append(os.path.join(os.getcwd(),'Resources/AnimationUI'))
os.path.join(os.getcwd(),'Resources/AnimationUI/image')
from Resources.AnimationUI import CountDown
from Resources.AnimationUI import MyBoneGap
from Resources.AnimationUI import MyFlipcorner
from Resources.AnimationUI import LegRotation
from Resources.AnimationUI import StylusSet
from Resources.AnimationUI import RingBtn
from Resources.AnimationUI import Flipcorner
from Resources.AnimationUI import Flipcorner_one
#
# NoImage
#

class MyEventFilter(qt.QObject):
    resize_single = qt.Signal()
    def eventFilter(self, obj, event):
        if event.type() == qt.QEvent.Resize:
            size = event.size()
            print("窗口大小改变")
            print(size)
            self.resize_single.emit()
            return True
        return False
class MySignals(qt.QObject):
  send_data_single = qt.Signal(str)
  InitChangePage_single = qt.Signal()
  MainChangePage_single = qt.Signal()
  PreparatChangeDownPage_single = qt.Signal()
  handleData_single = qt.Signal([str,np.ndarray])

# class Worker(qt.QRunnable):
#   send_data_single = qt.Signal(str)
#   def __init__(self):
#     super(Worker,self).__init__()

#   def run(self):
#     HOST = '192.168.3.31' # 服务端 IP 地址
#     PORT = 8898        # 服务端端口号
#     # 创建一个 TCP 套接字
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     # 绑定 IP 地址和端口号
#     server_socket.bind((HOST, PORT))
#     # 监听客户端连接请求
#     server_socket.listen(1)
#     print(f"Server is listening on {HOST}:{PORT}...")
#     a = 1
#     while True:
#       if a == 0:
#         break
#     # 等待客户端连接
#       client_socket, addr = server_socket.accept()
#       while 1:
#         # 接收客户端发送的数据
#         data = client_socket.recv(1024)
#         data = data.decode('utf-8')
#         # print(data)
#         if data != '':
#           self.send_data_single.emit(data)
#         else:
#           print("空")
#           break
#       # 关闭客户端连接
#       client_socket.close()

# class MyLoop(qt.QObject):
#   socketthread = qt.QThreadPool()
#   print("222222")
#   socketthread.setMaxThreadCount(1)

class NoImage(ScriptedLoadableModule):

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "NoImage"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"

   
class NoImageWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):

  def __init__(self, parent=None):

    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    # uiWidget = slicer.util.loadUI(self.resourcePath('UI/NoImage.ui'))
    self.uiPath = os.path.join(os.path.dirname(__file__), 'NewUI')
    uiWidget = slicer.util.loadUI(self.uiPath+'/newmain111_配准withImagge.ui')
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)
    self.ui.pushButton_1.hide()

    self.mysingle = MySignals()
    self.mysingle.send_data_single.connect(self.VRControl)
    self.mysingle.InitChangePage_single.connect(self.InitChangePage)
    self.mysingle.MainChangePage_single.connect(self.MainChangePage)
    self.mysingle.PreparatChangeDownPage_single.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget))
    self.mysingle.handleData_single.connect(self.handleData)
    self.VRstate = False
    self.updatetimer = qt.QTimer()
    self.updatetimer.timeout.connect(self.updatauiuiui)
    self.updatetimer.start(0.01)
    self.socket_thread = threading.Thread(target=self.creat_socket)
    self.socket_thread.start()


    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)
    #----------------------------------------------------------------------------------------
    self.newImgPath = os.path.join(os.path.dirname(__file__), 'Resources/AnimationUI/image')
    self.mainImgPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons/mainImage')
    self.iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons/NoImageIcon')
    self.FilePath = os.path.join(os.path.dirname(__file__), 'ssmdata')
    self.jiatiPath = os.path.join(os.path.dirname(__file__), '假体库')
    self.noimageWidget = slicer.util.findChild(slicer.util.mainWindow(),"NoImageWidget")
    self.FourWidget = slicer.util.findChild(slicer.util.mainWindow(),"widget")
    self.l_gugu_jiati = ['femur-l1-5','femur-l2','femur-l2-5','femur-l3','femur-l4','femur-l5']
    self.r_gugu_jiati = ['femur-R1-5','femur-R2','femur-R2-5','femur-R3','femur-R4','femur-R5']
    self.dianpian_jiati = ['Insert-1-5','Insert-2','Insert-2-5','Insert-3','Insert-4','Insert-5']
    self.jinggu_jiati = ['Tibia-1-5','Tibia-2','Tibia-2-5','Tibia-3','Tibia-4','Tibia-5']
    self.interactorNum = 0
    self.JingGu = 0
    self.TibiaJtSelectNum=0
    self.pyqt_data_x = []
    self.pyqt_data_y1 = []
    self.pyqt_data_y2 = []
    self.all_points = ['H点1','A点1','外侧远端1','内侧远端1','内侧后髁1','外侧后髁1','外侧皮质高点1','开髓点1','外侧凸点1','内侧凹点1','股骨头球心1','胫骨隆凸1','胫骨结节1','踝穴中心1','外侧高点1','内侧高点1']
    self.A1 = 4.5
    self.B1 = 0.5
    self.C1 = 3.5
    self.D1 = 0.0
    #['H点1','A点1','外侧远端1','内侧远端1','内侧后髁1','外侧后髁1','外侧皮质高点1','开髓点1','外侧凸点1','内侧凹点1','股骨头球心1','胫骨隆凸1','胫骨结节1','踝穴中心1','外侧高点1','内侧高点1']
    for i in range(141):
      self.pyqt_data_x.append(i-10)
      self.pyqt_data_y1.append(-5)
      self.pyqt_data_y2.append(5)
    # self.resizeEvent = ReSizeEvent()#自适应
    self.mainpageconnect()
    #设置默认页面
    self.ui.centerWidget.setCurrentIndex(0)
    self.ui.pushButton_0.setChecked(True)
    self.ui.stackedWidget.setCurrentIndex(0)
    self.ui.stackedWidget_2.setCurrentIndex(0)
    self.onPrepare()

    self.pagechangeconnect()
    self.change_jiati_btn_connect()
    self.peizhun3DView()
    self.peizhunpage()
    self.actionAnimationUI()

  def updatauiuiui(self):
    pass
#主界面图标----------------------------------------------------------------------------------
  def mainpageconnect(self):
    btns = [self.ui.pushButton_0,self.ui.pushButton_2,self.ui.pushButton_3,self.ui.pushButton_4,self.ui.pushButton_5,self.ui.pushButton_6]
    for i in range(len(btns)):
      self.mainbtn_icon(btns[i],'/%d'%(i+1),100)
    btns_bottom = [self.ui.pushButton_14,self.ui.pushButton_15,self.ui.pushButton_16,self.ui.pushButton_17,self.ui.pushButton_18,self.ui.pushButton]
    for i in range(len(btns_bottom)):
      self.mainbtn_icon(btns_bottom[i],'/%d'%(i+14),40)
  #切换假体按钮样式
  def mainbtn_icon(self,btn,imgpath,hight):
    # width = btn.rect.size().width()  #按钮宽度
    # hight= btn.rect.size().height()  #按钮长度
    # hight = 100
    btn.setIconSize(qt.QSize(hight,hight))
    btn.setIcon(qt.QIcon(qt.QPixmap(self.mainImgPath+imgpath+'.png').scaled(hight ,hight, qt.Qt.KeepAspectRatio, qt.Qt.SmoothTransformation)))
    # btn.setStyleSheet("icon-size: 60px;padding: 10px;text-align:top;}")

    #页面切换按钮----------------------------------------------------------------------------------
  def pagechangeconnect(self):
    #顶部按钮
    self.ui.pushButton_0.clicked.connect(lambda:self.BtnChangePage(self.ui.pushButton_0))
    self.ui.pushButton_2.clicked.connect(lambda:self.BtnChangePage(self.ui.pushButton_2))
    self.ui.pushButton_3.clicked.connect(lambda:self.BtnChangePage(self.ui.pushButton_3))
    self.ui.pushButton_4.clicked.connect(lambda:self.BtnChangePage(self.ui.pushButton_4))
    self.ui.pushButton_5.clicked.connect(lambda:self.BtnChangePage(self.ui.pushButton_5))
    self.ui.pushButton_6.clicked.connect(lambda:self.BtnChangePage(self.ui.pushButton_6))
    self.ui.pushButton_7.clicked.connect(lambda:self.BtnChangePage(self.ui.pushButton_7))
    #初始化界面
    self.ui.next_init_Btn.connect('clicked(bool)',self.InitChangePage)
    self.ui.Apply.connect('clicked(bool)',self.MainChangePage)
    #引导界面------------------
    #向下
    self.ui.D_nextBtn_1.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget))
    self.ui.D_nextBtn_2.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget))
    self.ui.D_nextBtn_3.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget))
    self.ui.D_nextBtn_4.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget))
    self.ui.D_nextBtn_5.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget))
    #向上
    self.ui.D_upBtn_1.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget))
    self.ui.D_upBtn_2.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget))
    self.ui.D_upBtn_3.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget))
    self.ui.D_upBtn_4.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget))
    self.ui.D_upBtn_5.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget))
    self.ui.changepageBtn.clicked.connect(self.MainChangePage)

    #切割页面------------------
    #向下
    # self.ui.D_nextBtn_6.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget_3))
    # self.ui.D_nextBtn_10.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget_3))
    # self.ui.D_nextBtn_11.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget_3))
    self.ui.pushButton_33.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget_3))
    #向上
    # self.ui.D_nextBtn_7.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget_3))
    # self.ui.D_nextBtn_8.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget_3))
    # self.ui.pushButton_24.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget_3))
    self.ui.pushButton_34.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget_3))
    #切割第四页------------------
    #向下
    # self.ui.pushButton_25.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget_10))
    self.ui.pushButton_28.clicked.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget_10))
    #向上
    self.ui.pushButton_30.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget_10))
    self.ui.pushButton_32.clicked.connect(lambda x:self.PreparatChangeUpPage(self.ui.stackedWidget_10))
        
    #股骨界面
    #---------------------------------------------------------------------------------------------

    # self.ui.PopupWidget.setVisible(False)
    # self.ui.head1.setVisible(False)
    # self.ui.OperationPlanWidget.setVisible(False)#手术规划每部分小界面
    # self.onState()
    # self.ui.OperationPlanWidget.setVisible(False)
    # self.ui.ForceWidget.setVisible(False)

    # #---------------初始化---------------------------------------------
    # self.ui.Apply.connect('clicked(bool)',self.onApply)
    # self.ui.StopSelect.connect('clicked(bool)', self.onStopSelect)
    # #手术技术
    # self.ui.CTMRI.toggled.connect(self.OperationTechnology)
    # self.ui.Deformation.toggled.connect(self.OperationTechnology)
    # #手术器械
    # self.ui.FourAndOne.toggled.connect(self.OperationTool)
    # self.ui.PSI.toggled.connect(self.OperationTool)
    # self.ui.ZhiWei.toggled.connect(self.OperationTool)
    # self.ui.ZhiXiang.toggled.connect(self.OperationTool)
    # #手术顺序
    # self.ui.TibiaFirst.toggled.connect(self.OperationOrder)
    # self.ui.FemurFirst.toggled.connect(self.OperationOrder)
    # #间隙平衡
    # self.ui.JieGu.toggled.connect(self.OperationClearance)
    # self.ui.RuanZuZhi.toggled.connect(self.OperationClearance)
    # #-------------------前进后退-------------------------------------
    # backPath = os.path.join(self.iconsPath, '后退.png')
    # self.ui.BackToolButton.setIcon(qt.QIcon(backPath))
    # #self.ui.BackToolButton.setEnabled(False)
    # forwardPath = os.path.join(self.iconsPath, '前进.png')
    # self.ui.ForwardToolButton.setIcon(qt.QIcon(forwardPath))
    # #self.ui.ForwardToolButton.setEnabled(False)
    # self.currentModel = 0
    # # self.WidgetList = [self.ui.InitWidget,self.ui.SystemPrepareWidget,self.ui.SSMWidget,self.ui.SSMWidget,self.ui.FemurToolWidget,self.ui.TibiaToolWidget,self.ui.ReportToolWidget,self.ui.NavigationToolWidget]
    # # self.LabelList = ["无","初始化","系统准备","股骨配准","胫骨配准","规划","规划","报告","导航","无"]
    # self.WidgetList = [self.ui.SystemPrepareWidget,self.ui.SSMWidget,self.ui.SSMWidget,self.ui.FemurToolWidget,self.ui.TibiaToolWidget,self.ui.NavigationToolWidget]
    # self.LabelList = ["无","系统准备","股骨配准","胫骨配准","手术规划","手术规划","导航","无"]
    # self.WidgetShow(self.currentModel)
    # self.ui.ReportToolWidget.setVisible(False)
    # self.ui.BackToolButton.connect('clicked(bool)',self.onBackToolButton)
    # self.ui.ForwardToolButton.connect('clicked(bool)',self.onForwardToolButton)

    # #--------------------------系统准备-----------------------------------------------------
    # #powerOnButton 手术准备 positionButton 系统准备 signInButton 工具设置 
    # #femurSystemButton 股骨侧 tibiaSystemButton 胫骨侧 test 校准检测
    # self.HideAllSystemWidget(self.ui.SystemWidget)
    # self.ui.powerOnButton.clicked.connect(lambda:self.onSystemButton(self.ui.powerOnButton))
    # self.ui.positionButton.clicked.connect(lambda:self.onSystemButton(self.ui.positionButton))
    # self.ui.signInButton.clicked.connect(lambda:self.onSystemButton(self.ui.signInButton))
    # self.ui.femurSystemButton.clicked.connect(lambda:self.onSystemButton(self.ui.femurSystemButton))
    # self.ui.tibiaSystemButton.clicked.connect(lambda:self.onSystemButton(self.ui.tibiaSystemButton))
    # self.ui.testButton.clicked.connect(lambda:self.onSystemButton(self.ui.testButton))
    # self.ui.SystemConfirm.clicked.connect(self.onSystemConfirm)
    # self.ui.SystemReset.clicked.connect(self.onSystemReset)
    # self.buttonMask("powerOn",self.ui.powerOnButton)
    # self.buttonMask("position",self.ui.positionButton)
    # self.buttonMask("signIn",self.ui.signInButton)
    # self.buttonMask("femurSystem",self.ui.femurSystemButton)
    # self.buttonMask("tibiaSystem",self.ui.tibiaSystemButton)
    # self.buttonMask("test",self.ui.testButton)
    # self.ui.SystemImage.setPixmap(qt.QPixmap(os.path.join(self.iconsPath,'SystemImage.png')))
    # self.ui.SystemImage.setScaledContents(True)


    # #------------配准（ssm模型）------------------------------------------------------------
  def peizhun3DView(self):
    layoutName = "Test3DView5"
    layoutLabel = "T5"
    layoutColor = [1.0, 1.0, 0.0]
    # ownerNode manages this view instead of the layout manager (it can be any node in the scene)
    viewOwnerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScriptedModuleNode")

    # Create MRML node
    viewLogic = slicer.vtkMRMLViewLogic()
    viewLogic.SetMRMLScene(slicer.mrmlScene)
    viewNode = viewLogic.AddViewNode(layoutName)
    viewNode.SetLayoutLabel(layoutLabel)
    viewNode.SetLayoutColor(layoutColor)
    viewNode.SetAndObserveParentLayoutNodeID(viewOwnerNode.GetID())
    # viewNode.SetBackgroundColor(0.1803921568627451, 0.2980392156862745, 0.4392156862745098)
    # viewNode.SetBackgroundColor2(0.1803921568627451, 0.2980392156862745, 0.4392156862745098)

    # Create widget
    self.viewWidget_peizhun = slicer.qMRMLThreeDWidget()
    self.viewWidget_peizhun.setMRMLScene(slicer.mrmlScene)
    self.viewWidget_peizhun.setMRMLViewNode(viewNode)
    # viewWidget.setParent(slicer.modules.noimage.widgetRepresentation().self().ui.widget_20)

    self.widget_2layout = qt.QHBoxLayout(self.ui.widget_2)
    self.widget_3layout = qt.QHBoxLayout(self.ui.widget_3)
    self.widget_2layout.addWidget(self.viewWidget_peizhun)
    self.img_label = qt.QLabel()
    self.widget_2layout.addWidget(self.img_label)
    self.widget_2layout.setStretch(0, 1)
    self.widget_2layout.setStretch(1, 1)
  
  def img_label_setimage(self,pixmap):
    self.img_label.setPixmap(pixmap)
    self.img_label.setScaledContents(True)


  def peizhunpage(self):
    # self.ui.Switch.connect('clicked(bool)',self.onSwitch)#显示切换
    self.ui.Confirm1.connect('clicked(bool)', self.onConfirm2)#确认
    self.ui.Select1.connect('clicked(bool)', self.onSelect1) #选取标志点
    self.ui.PointReset.clicked.connect(self.onPointReset)#重置
    self.ui.StopSelect.clicked.connect(self.onStopSelect)#停止
    self.ui.NextArea.clicked.connect(self.onNextArea)#下一区域
    self.SwitchState = 1
    femurPointCheckBox = [self.ui.femurPoint1,self.ui.femurPoint2,self.ui.femurPoint3,self.ui.femurPoint4,self.ui.femurPoint5,
                          self.ui.femurPoint6,self.ui.femurPoint7,self.ui.femurPoint8,self.ui.femurPoint9,self.ui.femurPoint10,
                          self.ui.femurPoint11,self.ui.femurPoint12,self.ui.femurPoint13,self.ui.femurPoint14]
    tibiaPointCheckBox = [self.ui.tibiaPoint1,self.ui.tibiaPoint2,self.ui.tibiaPoint3,self.ui.tibiaPoint4,self.ui.tibiaPoint5,
                          self.ui.tibiaPoint6,self.ui.tibiaPoint7,self.ui.tibiaPoint8,self.ui.tibiaPoint9]
    for i in range(0,len(femurPointCheckBox)):
      femurPointCheckBox[i].setEnabled(False)
    for i in range(0,len(tibiaPointCheckBox)):
      tibiaPointCheckBox[i].setEnabled(False)
    

  



  #链接开启脚踏板
  def StartPedal(self):
    # pushButton_change=[self.ui.Select1,self.ui.NextArea,self.ui.GuGuTou,self.ui.HPoint,self.ui.GuGuTouConfirm,self.ui.PointReset,self.ui.Confirm1]
    # index=[[0,2,3,4,5,6],[0,1,2,3,4,5,6],[0,5,6],[0,1,5,6]]
    # self.Pedal1=Pedal(pushButton_change,index)

    shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+Alt+Q"), slicer.util.mainWindow())
    shortcut.connect('activated()', self.OnPedalLeft)

    shortcut1 = qt.QShortcut(qt.QKeySequence("Ctrl+Alt+E"), slicer.util.mainWindow())
    shortcut1.connect('activated()', self.OnPedalRight)
    # # 0为选取单个点，1为选取点个点结束，2为
    # self.currentStatue=-1
    # self.pushButton_change=[self.ui.Select1,self.ui.GuGuTou,self.ui.HPoint,self.ui.GuGuTouConfirm,self.ui.PointReset,self.ui.Confirm1]

  def selectPushbutton_Femur(self):
    for i in range(len(self.pushButton_change)):
      self.pushButton_change[i].setStyleSheet("")

    if self.currentStatue==4:
      self.currentStatue=-1
    self.currentStatue+=1
    self.pushButton_change[self.currentStatue].setStyleSheet("background-color:red")



  #脚踏板左键响应函数
  def OnPedalLeft(self):
    # self.selectPushbutton_Femur()
    nIndex = self.ui.centerWidget.currentIndex
    if nIndex==3:
      self.onSelect1()

    if nIndex==4:
      self.onSelect1()

  #脚踏板右键响应函数
  def OnPedalRight(self):
    nIndex = self.ui.centerWidget.currentIndex
    if nIndex==3:
      if self.FemurPng - 1>10:
        self.onNextArea()
      if self.FemurPng - 1>16:
        self.onConfirm2()
    if nIndex==4:
      if self.TibiaPng - 1>6:
        self.onNextArea()
      if self.TibiaPng - 1>9:
        self.onConfirm2()
    # nIndex = self.ui.centerWidget.currentIndex
    # self.pushButton_change[self.currentStatue].click()







  #假体切换槽函数
  def change_jiati_btn_connect(self):
    self.ui.pushButton_8.clicked.connect(self.change_gugu_jiati_sub)
    self.ui.pushButton_9.clicked.connect(self.change_gugu_jiati_add)
    self.ui.pushButton_12.clicked.connect(self.change_jinggu_jiati_sub)
    self.ui.pushButton_13.clicked.connect(self.change_jinggu_jiati_add)

    self.ui.pushButton_8.pressed.connect(lambda:self.change_pressed_style(self.ui.pushButton_8,'/left2'))
    self.ui.pushButton_8.released.connect(lambda:self.change_released_style(self.ui.pushButton_8,'/left1'))
    self.ui.pushButton_9.pressed.connect(lambda:self.change_pressed_style(self.ui.pushButton_9,'/right2'))
    self.ui.pushButton_9.released.connect(lambda:self.change_released_style(self.ui.pushButton_9,'/right1'))
    self.ui.pushButton_12.pressed.connect(lambda:self.change_pressed_style(self.ui.pushButton_12,'/left2'))
    self.ui.pushButton_12.released.connect(lambda:self.change_released_style(self.ui.pushButton_12,'/left1'))
    self.ui.pushButton_13.pressed.connect(lambda:self.change_pressed_style(self.ui.pushButton_13,'/right2'))
    self.ui.pushButton_13.released.connect(lambda:self.change_released_style(self.ui.pushButton_13,'/right1'))
    self.change_pressed_style(self.ui.pushButton_8,'/left1')
    self.change_pressed_style(self.ui.pushButton_9,'/right1')
    self.change_pressed_style(self.ui.pushButton_12,'/left1')
    self.change_pressed_style(self.ui.pushButton_13,'/right1')
    self.change_pressed_style(self.ui.pushButton_10,'/left1')
    self.change_pressed_style(self.ui.pushButton_11,'/right1')
  #切换假体按钮样式
  def change_pressed_style(self,btn,imgpath):
    # width = btn.rect.size().width()  #按钮宽度
    # hight= btn.rect.size().height()  #按钮长度
    hight = 42
    btn.setIconSize(qt.QSize(hight,hight))
    btn.setIcon(qt.QIcon(qt.QPixmap(self.newImgPath+imgpath+'.png').scaled(hight ,hight, qt.Qt.KeepAspectRatio, qt.Qt.SmoothTransformation)))
  #切换假体按钮样式
  def change_released_style(self,btn,imgpath):
    # width = btn.rect.size().width()  #按钮宽度
    # hight= btn.rect.size().height()  #按钮长度
    hight = 42
    btn.setIconSize(qt.QSize(hight,hight))
    btn.setIcon(qt.QIcon(qt.QPixmap(self.newImgPath+imgpath+'.png').scaled(hight ,hight, qt.Qt.KeepAspectRatio, qt.Qt.SmoothTransformation)))


  #切换股骨假体后修改屈膝状态下股骨假体位置
  def ChangeJTQuxiTrans(self):
    Ftransform3 = slicer.util.getNode('trans_quxi')
    dis_list=[[11,15],[11,17],[12,18],[13,19],[14,20],[17,21]]
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      index=self.l_gugu_jiati.index(self.FemurL)
    else:
      index=self.r_gugu_jiati.index(self.FemurR)
    Ftrans1 = np.array([[1, 0, 0, 0],
                        [0, 0, -1, dis_list[index][0]],
                        [0, 1, 0, dis_list[index][1]],
                        [0, 0, 0, 1]])

    Ftransform3.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans1))



  #股骨假体型号切换向右
  def change_gugu_jiati_add(self):
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      index = self.l_gugu_jiati.index(self.FemurL)
      # if index == 0:
      #   self.FemurL = self.l_gugu_jiati[-1]
      if index == len(self.l_gugu_jiati)-1:
        self.FemurL = self.l_gugu_jiati[0]
      else:
        self.FemurL = self.l_gugu_jiati[index+1]
      self.ui.label_21.setText(self.FemurL)
      self.loadJiaTi(self.FemurL)
    else:
      index = self.r_gugu_jiati.index(self.FemurR)
      # if index == 0:
      #   self.FemurR = self.r_gugu_jiati[-1]
      if index == len(self.r_gugu_jiati)-1:
        self.FemurR = self.r_gugu_jiati[0]
      else:
        self.FemurR = self.r_gugu_jiati[index+1]
      self.ui.label_21.setText(self.FemurR)
      self.loadJiaTi(self.FemurR)
    #切换股骨假体后修改屈膝状态下股骨假体位置
    self.ChangeJTQuxiTrans()
  #股骨假体型号切换向左
  def change_gugu_jiati_sub(self):
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      index = self.l_gugu_jiati.index(self.FemurL)
      if index == 0:
        self.FemurL = self.l_gugu_jiati[-1]
      # if index == len(self.l_gugu_jiati)-1:
      #   self.FemurL = self.l_gugu_jiati[0]
      else:
        self.FemurL = self.l_gugu_jiati[index-1]
      self.ui.label_21.setText(self.FemurL)
      self.loadJiaTi(self.FemurL)
    else:
      index = self.r_gugu_jiati.index(self.FemurR)
      if index == 0:
        self.FemurR = self.r_gugu_jiati[-1]
      # if index == len(self.r_gugu_jiati)-1:
      #   self.FemurR = self.r_gugu_jiati[0]
      else:
        self.FemurR = self.r_gugu_jiati[index-1]
      self.ui.label_21.setText(self.FemurR)
      self.loadJiaTi(self.FemurR)
    #切换股骨假体后修改屈膝状态下股骨假体位置
    self.ChangeJTQuxiTrans()
  #胫骨假体型号切换向右
  def change_jinggu_jiati_add(self):
    index = self.jinggu_jiati.index(self.TibiaJiaTi)
    if index == len(self.jinggu_jiati)-1:
      self.TibiaJiaTi = self.jinggu_jiati[0]
    else:
      self.TibiaJiaTi = self.jinggu_jiati[index+1]
    self.ui.label_23.setText(self.TibiaJiaTi)
    self.loadTibiaJiaTi(self.TibiaJiaTi)
    self.loadChenDian()
  #胫骨假体型号切换向左
  def change_jinggu_jiati_sub(self):
    index = self.jinggu_jiati.index(self.TibiaJiaTi)
    if index == 0:
      self.TibiaJiaTi = self.jinggu_jiati[-1]
    else:
      self.TibiaJiaTi = self.jinggu_jiati[index-1]
    self.ui.label_23.setText(self.TibiaJiaTi)
    self.loadTibiaJiaTi(self.TibiaJiaTi)
    self.loadChenDian()

  #动态UI
  def actionAnimationUI(self):
    #系统准备
    self.preparatPage_Animationui()
    #股骨配准
    self.lay_w27 = qt.QHBoxLayout(self.ui.widget_27)
    self.lay_w26 = qt.QHBoxLayout(self.ui.widget_26)
    #膝关节评估
    self.pinggu_Animationui()
    self.pinggu_connect()
    self.ui.pushButton_20.setChecked(1)
    self.pinggu_btn_clicked(self.ui.pushButton_20)
    #手术规划
    self.planning_Animationui()
    self.view_3D_1()
    self.view_3D_2()
    self.view_3D_ringbtn()
    self.planning_btn_connect()
    #切割
    self.cut_Animationui()
    self.cut_connect()


#-------------------页面切换（开始）--------------------------------------------------
  #主页面切换(通过顶部按钮)
  def BtnChangePage(self,btn):
    index = int(btn.objectName[-1])
    self.ui.centerWidget.setCurrentIndex(index) #设置页面
    self.status_TopBtn(index)
    if index == 3:
      self.WidgetShow(1)
    if index == 4:
      self.WidgetShow(2)
    #切换页面时改变观察者状态
    self.OpenOrCloseObserveByIndex()
  #顶部按钮状态
  def status_TopBtn(slef,index):
    btns = slicer.modules.noimage.widgetRepresentation().self().ui.widget13.findChildren('QPushButton')
    for btn in btns:
      if int(btn.objectName[-1]) == index:
        btn.setChecked(True)
      else:
        btn.setChecked(False)
  #主页面切换
  def MainChangePage(self):
    num = self.ui.centerWidget.count #总页数
    nIndex = self.ui.centerWidget.currentIndex #当前页面索引
    if nIndex == 0:
      if self.ui.CTMRI.checked:
        self.onApply()
      else:
        nIndex += 1
    nIndex += 1
    if nIndex >= num:
      nIndex = 0 #第0页暂时不用
    self.ui.centerWidget.setCurrentIndex(nIndex) #设置页面
    if not nIndex == 1:
      self.status_TopBtn(nIndex)
    if nIndex == 3:
      if self.ui.CTMRI.checked:
        self.ui.gugupoints.hide()
        # self.ui.widget_2.hide()
        self.ui.gugu.layout().addWidget(slicer.modules.withimage.widgetRepresentation().self().ui.femurPointWidget)
        # slicer.modules.withimage.widgetRepresentation().self().ui.femurPointWidget.setMaximumWidth(394)
        slicer.modules.withimage.widgetRepresentation().self().ui.femurPointWidget.layout().addWidget(slicer.modules.withimage.widgetRepresentation().self().ui.widget_10)
        slicer.modules.withimage.widgetRepresentation().self().ui.femurPointWidget.layout().setStretch(9,5)
        # slicer.modules.withimage.widgetRepresentation().self().ui.widget_10.layout().addItem(qt.QSpacerItem(20,200))
        # slicer.modules.withimage.widgetRepresentation().self().ui.widget_10.setStyleSheet("QPushButton{font: 16pt 华文中宋;border:1px solid #c8c8c8;border-radius:0px;background-color: rgb(46, 76, 112);height:40px;}""QPushButton::pressed{background:#6db1fa;}")
        # self.ui.gugu.layout().addWidget(slicer.app.layoutManager().threeDWidget(0).threeDView().parent().parent())
        self.ui.gugu.layout().removeWidget(self.ui.widget_2)
        self.ui.gugu.layout().addWidget(self.ui.widget_2)
        self.ui.gugu.layout().setStretch(2,16)
      else:
        self.WidgetShow(1)
    if nIndex == 4:
      if self.ui.CTMRI.checked:
        self.ui.jinggupoints.hide()
        self.ui.widget_3.hide()
        self.ui.jinggu.layout().addWidget(slicer.modules.withimage.widgetRepresentation().self().ui.tibiaPointWidget)
        # slicer.modules.withimage.widgetRepresentation().self().ui.tibiaPointWidget.setMaximumWidth(394)
        slicer.modules.withimage.widgetRepresentation().self().ui.tibiaPointWidget.layout().addWidget(slicer.modules.withimage.widgetRepresentation().self().ui.widget_10)
        slicer.modules.withimage.widgetRepresentation().self().ui.tibiaPointWidget.layout().setStretch(6,5)
        # slicer.modules.withimage.widgetRepresentation().self().ui.widget_10.layout().addItem(qt.QSpacerItem(20,200))
        # slicer.modules.withimage.widgetRepresentation().self().ui.widget_10.setStyleSheet("QPushButton{font: 16pt 华文中宋;border:1px solid #c8c8c8;border-radius:0px;background-color: rgb(46, 76, 112);height:40px;}""QPushButton::pressed{background:#6db1fa;}")
        # self.ui.jinggu.layout().addWidget(slicer.app.layoutManager().threeDWidget(0).threeDView().parent().parent())
        # self.ui.gugu.layout().removeWidget(self.ui.widget_2)
        self.ui.jinggu.layout().addWidget(self.ui.widget_2)
        self.ui.jinggu.layout().setStretch(3,16)
        slicer.modules.withimage.widgetRepresentation().self().ui.tibiaPointWidget.show()
      else:
        self.WidgetShow(2)
    # print("pppp",self.ui.centerWidget.currentIndex)
    self.OpenOrCloseObserveByIndex()

  #双目观察者需要在第5页开启，第6页关闭
  def OpenOrCloseObserveByIndex(self):
    nIndex = self.ui.centerWidget.currentIndex #当前页面索引
    #第3、4页，配准时，相机需要跟随针尖
    if nIndex==3:
      rotationTransformNode = slicer.util.getNode('StylusTipToStylus')
      view1 = self.viewWidget_peizhun.threeDView()
      cameraNode = view1.cameraNode()
      cameraNode.SetAndObserveTransformNodeID(rotationTransformNode.GetID())
      cameraNode.SetPosition(29.063498635140363, 180.79209969950026, -465.26286090051354)
      cameraNode.SetFocalPoint(0,0,0)
      cameraNode.SetViewUp(0.0488375470975232, 0.9299557672972033, 0.3644134531876765)

    if nIndex==5:
      print("开启观察者")
      rotationTransformNode = slicer.util.getNode('DianjiToTracker1')
      try:
        self.removeObserver(rotationTransformNode,vtk.vtkCommand.ModifiedEvent, self.caculateLowPoint)
      except:
        pass
      self.addObserver(rotationTransformNode,vtk.vtkCommand.ModifiedEvent, self.caculateLowPoint)

    if nIndex==6:
      try:
        print("关闭观察者")
        rotationTransformNode = slicer.util.getNode('DianjiToTracker1')
        self.removeObserver(rotationTransformNode,vtk.vtkCommand.ModifiedEvent, self.caculateLowPoint)
      except:
        pass
  #初始化页面切换
  def InitChangePage(self):
    num = self.ui.stackedWidget_2.count #总页数
    nIndex = self.ui.stackedWidget_2.currentIndex #当前页面索引
    nIndex += 1
    if nIndex >= num:
      nIndex = num-1
    self.ui.stackedWidget_2.setCurrentIndex(nIndex) #设置页面
  #页面切换(向下)
  def PreparatChangeDownPage(self,stackedwidget):
    num = stackedwidget.count #总页数
    nIndex = stackedwidget.currentIndex #当前页面索引
    nIndex += 1
    if nIndex >= num:
      nIndex = num-1
    stackedwidget.setCurrentIndex(nIndex) #设置页面
  #页面切换(向上)
  def PreparatChangeUpPage(self,stackedwidget):
    nIndex = stackedwidget.currentIndex #当前页面索引
    nIndex -= 1
    if nIndex < 0:
      nIndex = 0
    stackedwidget.setCurrentIndex(nIndex) #设置页面
  
  #股骨配准点击确认跳转到胫骨配准
  def gugu2jinggu(self):
    self.MainChangePage()
    self.widget_2layout.removeWidget(self.viewWidget_peizhun)
    self.widget_2layout.removeWidget(self.img_label)
    self.widget_3layout.addWidget(self.viewWidget_peizhun)
    self.widget_3layout.addWidget(self.img_label)
    self.widget_3layout.setStretch(0, 1)
    self.widget_3layout.setStretch(1, 1)

  #胫骨配准点击确认跳转到膝关节评估
  def jinggu2pinggu(self):
    self.MainChangePage()
    #计算屈膝角，内外翻角
    self.AddSuiDongAxis()
    # rotationTransformNode = slicer.util.getNode('DianjiToTracker1')
    # self.ZuiDiDian = rotationTransformNode.AddObserver(
    #   slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.caculateLowPoint)

  #膝关节评估点击保存跳转到手术规划
  def pinggu2guihua(self):
    self.MainChangePage() #切换页面
    self.onParameter()#建立坐标系推荐假体，并放置在合理位置
    self.onAdjustment()#添加第三刀平面
    self.onAdjustment2()
    self.loadChenDian() #加载垫片
    self.leftviewcenter()#左侧三维视窗居中
    self.rightviewcenter()#右侧三维视窗居中
    slicer.modules.popup.widgetRepresentation().self().onConfirm()
    slicer.modules.tibiapopup.widgetRepresentation().self().onConfirm()
    jinggu = slicer.util.getNode("胫骨切割") #显示胫骨切割
    jinggu.SetDisplayVisibility(1)
    self.ui.pushButton_51.setChecked(1)
    self.ui.pushButton_44.setChecked(1)
    self.ui.pushButton_45.setChecked(1)
    self.ui.pushButton_46.setChecked(1)

#-------------------页面切换（结束）--------------------------------------------------

#-------------------------系统准备（开始）-----------------------------------------------
  #系统准备动态UI
  def preparatPage_Animationui(self):
    self.countdown = CountDown.CountDown()
    # self.countdown.setMinimumSize(400,400)
    # self.countdown.setMaximumSize(400,400)
    # self.countdown.update(400,400)
    self.countdown.end.connect(lambda x:self.PreparatChangeDownPage(self.ui.stackedWidget))
    self.ui.D_nextBtn_4.clicked.connect(self.countdown.timer_start)
    layout = qt.QHBoxLayout(self.ui.widget_31)
    layout.addWidget(self.countdown)
#-------------------------系统准备（结束）-----------------------------------------------

#-------------------------膝关节评估（开始）-----------------------------------------------
  #膝关节评估添加动态UI
  def pinggu_Animationui(self):
    #第一页
    self.leg_rotation = LegRotation.LegRotation() #腿部旋转ui
    self.flipcorner = MyFlipcorner.MyFlipcorner() #记录角度ui
    self.flipcorner.graphicsview.setSceneRect(qt.QRectF(0,100,1,1))
    self.flipcorner.graphicsview.scale(1.3,1.3)
    self.flipcorner_0_90 = Flipcorner.Flipcorner()#记录0和90°间隙ui
    lay1 = qt.QHBoxLayout(self.ui.widget_32)
    lay1.addWidget(self.leg_rotation)
    #--------------------------------------------------------
    lay2 = qt.QVBoxLayout(self.ui.widget_33)
    lay2.addWidget(self.flipcorner)
    ####
    lay2_1 = qt.QHBoxLayout(self.ui.widget_33)
    horizontalSpacer = qt.QSpacerItem(200, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay2_1.addItem(horizontalSpacer)
    self.pinggu_allclear_btn = qt.QPushButton(self.ui.widget_33)
    self.pinggu_allclear_btn.setMinimumSize(100,42)
    self.pinggu_allclear_btn.setText("全部清除")
    self.pinggu_allclear_btn.clicked.connect(lambda:self.clearallmark(self.flipcorner))
    lay2_1.addWidget(self.pinggu_allclear_btn)
    lay2_1.setContentsMargins(0, 0, 50, 20)
    lay2.addItem(lay2_1)
    #--------------------------------------------------------
    lay3 = qt.QVBoxLayout(self.ui.widget_34)
    lay3.addWidget(self.flipcorner_0_90)
    ####
    lay3_2 = qt.QHBoxLayout(self.ui.widget_34)
    self.label_wwcqg = qt.QLabel(self.ui.widget_34)
    self.label_wwcqg.setMinimumWidth(400)
    self.label_wwcqg.setText("未完成切割")
    self.label_wwcqg.setAlignment(qt.Qt.AlignCenter)
    self.label_wwcqg.setStyleSheet("background-color: rgba(255, 255, 255, 30);border-color: rgba(255, 255, 255, 30);border-radius:5px;color: rgba(255, 255, 255, 200);")
    horizontalSpacer1 = qt.QSpacerItem(20, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    horizontalSpacer2 = qt.QSpacerItem(20, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay3_2.addItem(horizontalSpacer1)
    lay3_2.addWidget(self.label_wwcqg)
    lay3_2.addItem(horizontalSpacer2)
    lay3.addItem(lay3_2)
    #####
    verticalSpacer = qt.QSpacerItem(20, 250, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
    lay3.addItem(verticalSpacer)
    lay3_1 = qt.QHBoxLayout(self.ui.widget_34)
    self.pinggu_save_btn = qt.QPushButton(self.ui.widget_34)
    self.pinggu_save_btn.setMinimumSize(100,42)
    self.pinggu_save_btn.setText("保存")
    horizontalSpacer = qt.QSpacerItem(200, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay3_1.addItem(horizontalSpacer)
    lay3_1.addWidget(self.pinggu_save_btn)
    lay3_1.setContentsMargins(0, 0, 50, 20)
    lay3.addItem(lay3_1)
    #第二页
    self.leg_rotation1 = LegRotation.LegRotation() #腿部旋转ui
    self.flipcorner1 = MyFlipcorner.MyFlipcorner() #记录角度ui
    self.flipcorner1.graphicsview.setSceneRect(qt.QRectF(0,100,1,1))
    self.flipcorner1.graphicsview.scale(1.3,1.3)
    self.flipcorner_0_90_1 = Flipcorner.Flipcorner()#记录0和90°间隙ui
    lay1 = qt.QHBoxLayout(self.ui.widget_24)
    lay1.addWidget(self.leg_rotation1)
    #--------------------------------------------------------
    lay2 = qt.QVBoxLayout(self.ui.widget_35)
    lay2.addWidget(self.flipcorner1)
    ####
    lay2_1 = qt.QHBoxLayout(self.ui.widget_35)
    horizontalSpacer = qt.QSpacerItem(200, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay2_1.addItem(horizontalSpacer)
    self.pinggu_allclear_btn1 = qt.QPushButton(self.ui.widget_35)
    self.pinggu_allclear_btn1.setMinimumSize(100,42)
    self.pinggu_allclear_btn1.setText("全部清除")
    self.pinggu_allclear_btn1.clicked.connect(lambda:self.clearallmark(self.flipcorner1))
    lay2_1.addWidget(self.pinggu_allclear_btn1)
    lay2_1.setContentsMargins(0, 0, 50, 20)
    lay2.addItem(lay2_1)
    #--------------------------------------------------------
    lay3 = qt.QVBoxLayout(self.ui.widget_36)
    lay3.addWidget(self.flipcorner_0_90_1)
    ####
    lay3_2 = qt.QHBoxLayout(self.ui.widget_36)
    self.label_wwcqg1 = qt.QLabel(self.ui.widget_36)
    self.label_wwcqg1.setMinimumWidth(400)
    self.label_wwcqg1.setText("未完成切割")
    self.label_wwcqg1.setAlignment(qt.Qt.AlignCenter)
    self.label_wwcqg1.setStyleSheet("background-color: rgba(255, 255, 255, 30);border-color: rgba(255, 255, 255, 30);border-radius:5px;color: rgba(255, 255, 255, 200);")
    horizontalSpacer1 = qt.QSpacerItem(20, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    horizontalSpacer2 = qt.QSpacerItem(20, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay3_2.addItem(horizontalSpacer1)
    lay3_2.addWidget(self.label_wwcqg1)
    lay3_2.addItem(horizontalSpacer2)
    lay3.addItem(lay3_2)
    #####
    verticalSpacer = qt.QSpacerItem(20, 250, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
    lay3.addItem(verticalSpacer)
    lay3_1 = qt.QHBoxLayout(self.ui.widget_36)
    self.pinggu_save_btn1 = qt.QPushButton(self.ui.widget_36)
    self.pinggu_save_btn1.setMinimumSize(100,42)
    self.pinggu_save_btn1.setText("保存")
    horizontalSpacer = qt.QSpacerItem(200, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay3_1.addItem(horizontalSpacer)
    lay3_1.addWidget(self.pinggu_save_btn1)
    lay3_1.setContentsMargins(0, 0, 50, 20)
    lay3.addItem(lay3_1)
    #第三页
    self.leg_rotation2 = LegRotation.LegRotation() #腿部旋转ui
    self.flipcorner2 = MyFlipcorner.MyFlipcorner() #记录角度ui
    self.flipcorner2.graphicsview.setSceneRect(qt.QRectF(0,100,1,1))
    self.flipcorner2.graphicsview.scale(1.3,1.3)
    self.flipcorner_0_90_2 = Flipcorner.Flipcorner()#记录0和90°间隙ui
    lay1 = qt.QHBoxLayout(self.ui.widget_37)
    lay1.addWidget(self.leg_rotation2)
    #--------------------------------------------------------
    lay2 = qt.QVBoxLayout(self.ui.widget_38)
    lay2.addWidget(self.flipcorner2)
    ####
    lay2_1 = qt.QHBoxLayout(self.ui.widget_38)
    horizontalSpacer = qt.QSpacerItem(200, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay2_1.addItem(horizontalSpacer)
    self.pinggu_allclear_btn2 = qt.QPushButton(self.ui.widget_38)
    self.pinggu_allclear_btn2.setMinimumSize(100,42)
    self.pinggu_allclear_btn2.setText("全部清除")
    self.pinggu_allclear_btn2.clicked.connect(lambda:self.clearallmark(self.flipcorner2))
    lay2_1.addWidget(self.pinggu_allclear_btn2)
    lay2_1.setContentsMargins(0, 0, 50, 20)
    lay2.addItem(lay2_1)
    #--------------------------------------------------------
    lay3 = qt.QVBoxLayout(self.ui.widget_39)
    lay3.addWidget(self.flipcorner_0_90_2)
    ####
    lay3_2 = qt.QHBoxLayout(self.ui.widget_39)
    self.label_wwcqg2 = qt.QLabel(self.ui.widget_39)
    self.label_wwcqg2.setMinimumWidth(400)
    self.label_wwcqg2.setText("未完成切割")
    self.label_wwcqg2.setAlignment(qt.Qt.AlignCenter)
    self.label_wwcqg2.setStyleSheet("background-color: rgba(255, 255, 255, 30);border-color: rgba(255, 255, 255, 30);border-radius:5px;color: rgba(255, 255, 255, 200);")
    horizontalSpacer1 = qt.QSpacerItem(20, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    horizontalSpacer2 = qt.QSpacerItem(20, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay3_2.addItem(horizontalSpacer1)
    lay3_2.addWidget(self.label_wwcqg2)
    lay3_2.addItem(horizontalSpacer2)
    lay3.addItem(lay3_2)
    #####
    verticalSpacer = qt.QSpacerItem(20, 250, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
    lay3.addItem(verticalSpacer)
    lay3_1 = qt.QHBoxLayout(self.ui.widget_39)
    self.pinggu_save_btn2 = qt.QPushButton(self.ui.widget_39)
    self.pinggu_save_btn2.setMinimumSize(100,42)
    self.pinggu_save_btn2.setText("保存")
    horizontalSpacer = qt.QSpacerItem(200, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
    lay3_1.addItem(horizontalSpacer)
    lay3_1.addWidget(self.pinggu_save_btn2)
    lay3_1.setContentsMargins(0, 0, 50, 20)
    lay3.addItem(lay3_1)
    # self.leg_rotation2 = LegRotation.LegRotation() #腿部旋转ui
    # self.flipcorner2 = MyFlipcorner.MyFlipcorner() #记录角度ui
    # self.flipcorner2.graphicsview.setSceneRect(qt.QRectF(0,100,1,1))
    # self.flipcorner2.graphicsview.scale(1.3,1.3)
    # self.flipcorner_0_90_2 = Flipcorner.Flipcorner()#记录0和90°间隙ui
    # lay1 = qt.QHBoxLayout(self.ui.widget_37)
    # lay1.addWidget(self.leg_rotation2)
    # lay2 = qt.QHBoxLayout(self.ui.widget_38)
    # lay2.addWidget(self.flipcorner2)
    # lay3 = qt.QVBoxLayout(self.ui.widget_39)
    # lay3.addWidget(self.flipcorner_0_90_2)
    # self.label_wwcqg_2 = qt.QLabel()
    # self.label_wwcqg_2.setText("未完成切割")
    # self.label_wwcqg_2.setAlignment(qt.Qt.AlignCenter)
    # self.label_wwcqg_2.setStyleSheet("background-color: rgba(255, 255, 255, 30);border-color: rgba(255, 255, 255, 30);border-radius:5px;color: rgba(255, 255, 255, 200);")
    # lay3.addWidget(self.label_wwcqg_2)
    # verticalSpacer = qt.QSpacerItem(20, 250, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
    # lay3.addItem(verticalSpacer)
    # self.pinggu_save_btn_2 = qt.QPushButton()
    # lay3.addWidget(self.pinggu_save_btn_2)
  def clearallmark(self,flipcorner):
    flipcorner.mark1.setRect(0,-10,0,0)
    flipcorner.angele_0_min = None
    flipcorner.angele_0_max = None
    flipcorner.mark2.setRect(0,-10,0,0)
    flipcorner.angele_1_min = None
    flipcorner.angele_1_max = None
    flipcorner.mark3.setRect(0,-10,0,0)
    flipcorner.angele_2_min = None
    flipcorner.angele_2_max = None


  #膝关节评估信号槽连接
  def pinggu_connect(self):
    self.ui.pushButton_20.clicked.connect(lambda x:self.pinggu_btn_clicked(self.ui.pushButton_20))
    self.ui.pushButton_21.clicked.connect(lambda x:self.pinggu_btn_clicked(self.ui.pushButton_21))
    self.ui.pushButton_22.clicked.connect(lambda x:self.pinggu_btn_clicked(self.ui.pushButton_22))
    self.pinggu_save_btn.clicked.connect(self.pinggu2guihua)
  #膝关节评估槽函数
  def pinggu_btn_clicked(self,btn):
    if btn.objectName == "pushButton_20":
      if btn.checked:
        self.ui.stackedWidget_5.setCurrentIndex(1)
        self.ui.pushButton_21.setChecked(0)
        self.ui.pushButton_22.setChecked(0)
    elif btn.objectName == "pushButton_21":
      if btn.checked:
        self.ui.stackedWidget_5.setCurrentIndex(0)
        self.ui.pushButton_20.setChecked(0)
        self.ui.pushButton_22.setChecked(0)
    else:
      if btn.checked:
        self.ui.stackedWidget_5.setCurrentIndex(2)
        self.ui.pushButton_20.setChecked(0)
        self.ui.pushButton_21.setChecked(0)
#-------------------------膝关节评估（结束）-----------------------------------------------

#----------------------手术规划（开始）-------------------------------------------------
  #手术规划添加动态UI
  def planning_Animationui(self):
    self.stylusset = StylusSet.StylusSet()
    layout = qt.QHBoxLayout(self.ui.widget_23)
    layout.addWidget(self.stylusset)

  def dayinprint(self):
    #左侧圆环按钮
    x = (self.ui.widget_20.rect.width() - 524)/2
    y = (self.ui.widget_20.rect.height() - 536)
    self.ringbtn_top.setGeometry(qt.QRect(110+int(x), 0, 300, 300))
    self.ringbtn_bottom.setGeometry(qt.QRect(110+int(x), 240+int(y), 300, 300))
    #右侧圆环按钮
    x2 = (self.ui.widget_22.rect.width() - 606)/2
    y2 = self.ui.widget_22.rect.height() - 534
    self.ringbtn_r_top.setGeometry(qt.QRect(170+int(x), 0, 300, 300))
    self.ringbtn_r_bottom.setGeometry(qt.QRect(170+int(x), 240+int(y), 300, 300)) 
    #stylusset
    # x3 = (self.ui.widget_23.rect.width() - 652)//50
    # y3 = (self.ui.widget_23.rect.height() - 596)//50
    # self.stylusset.graphicsview.scale(1+0.1*x3, 1+0.1*y3)

  #手术规划三维视窗
  def view_3D_1(self):
    layoutName = "Test3DView"
    layoutLabel = "T3"
    layoutColor = [1.0, 1.0, 0.0]
    # ownerNode manages this view instead of the layout manager (it can be any node in the scene)
    viewOwnerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScriptedModuleNode")

    # Create MRML node
    viewLogic = slicer.vtkMRMLViewLogic()
    viewLogic.SetMRMLScene(slicer.mrmlScene)
    viewNode = viewLogic.AddViewNode(layoutName)
    viewNode.SetLayoutLabel(layoutLabel)
    viewNode.SetLayoutColor(layoutColor)
    viewNode.SetAndObserveParentLayoutNodeID(viewOwnerNode.GetID())
    viewNode.SetBackgroundColor(0.1803921568627451, 0.2980392156862745, 0.4392156862745098)
    viewNode.SetBackgroundColor2(0.1803921568627451, 0.2980392156862745, 0.4392156862745098)
    # viewNode.SetBackgroundColor(0, 1, 1)
    # viewNode.SetBackgroundColor2(0, 1, 1)

    # Create widget
    self.viewWidget1 = slicer.qMRMLThreeDWidget()
    self.viewWidget1.setMRMLScene(slicer.mrmlScene)
    self.viewWidget1.setMRMLViewNode(viewNode)
    # viewWidget.setParent(slicer.modules.noimage.widgetRepresentation().self().ui.widget_20)

    # layout = qt.QHBoxLayout(self.ui.widget_20)
    # layout.addWidget(viewWidget)
    # self.viewWidget1.setParent(self.ui.widget_20)
    # self.viewWidget1.setGeometry(qt.QRect(0, 0, 510, 498))

    layout = qt.QHBoxLayout(self.ui.widget_20)
    layout.addWidget(self.viewWidget1)
    #窗口尺寸修改====================================================
    self.eventfliter = MyEventFilter()
    self.eventfliter.resize_single.connect(self.dayinprint)
    self.viewWidget1.installEventFilter(self.eventfliter)

  def view_3D_2(self):
    layoutName = "Test3DView2"
    layoutLabel = "T4"
    layoutColor = [1.0, 1.0, 0.0]
    # ownerNode manages this view instead of the layout manager (it can be any node in the scene)
    viewOwnerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScriptedModuleNode")

    # Create MRML node
    viewLogic = slicer.vtkMRMLViewLogic()
    viewLogic.SetMRMLScene(slicer.mrmlScene)
    viewNode = viewLogic.AddViewNode(layoutName)
    viewNode.SetLayoutLabel(layoutLabel)
    viewNode.SetLayoutColor(layoutColor)
    viewNode.SetAndObserveParentLayoutNodeID(viewOwnerNode.GetID())
    viewNode.SetBackgroundColor(0.1803921568627451, 0.2980392156862745, 0.4392156862745098)
    viewNode.SetBackgroundColor2(0.1803921568627451, 0.2980392156862745, 0.4392156862745098)

    # Create widget
    self.viewWidget2 = slicer.qMRMLThreeDWidget()
    self.viewWidget2.setMRMLScene(slicer.mrmlScene)
    self.viewWidget2.setMRMLViewNode(viewNode)
    # viewWidget.setParent(slicer.modules.noimage.widgetRepresentation().self().ui.widget_20)

    layout = qt.QHBoxLayout(self.ui.widget_22)
    layout.addWidget(self.viewWidget2)

  def view_3D_ringbtn(self):
    #左侧股骨
    self.show_ringbtn_top_btn = qt.QPushButton(self.ui.widget_20)
    self.show_ringbtn_top_btn.setStyleSheet("border:none;background-color:rgba(0,0,0,0);")
    self.show_ringbtn_top_btn.setGeometry(qt.QRect(105, 0, 300, 200))
    self.show_ringbtn_top_btn.clicked.connect(self.show_ringbtn_top_slot)
    self.ringbtn_top = RingBtn.MyRingBtn(self.ui.widget_20)
    self.ringbtn_top.setGeometry(qt.QRect(110, 0, 300, 300))
    #左侧胫骨
    self.show_ringbtn_bottom_btn = qt.QPushButton(self.ui.widget_20)
    self.show_ringbtn_bottom_btn.setStyleSheet("border:none;background-color:rgba(0,0,0,0);")
    self.show_ringbtn_bottom_btn.setGeometry(qt.QRect(105, 310, 300, 200))
    self.show_ringbtn_bottom_btn.clicked.connect(self.show_ringbtn_bottom_slot)
    self.ringbtn_bottom = RingBtn.MyRingBtn(self.ui.widget_20)
    self.ringbtn_bottom.setGeometry(qt.QRect(110, 240, 300, 300))
    self.ringbtn_bottom.hide()
    #右侧股骨
    self.show_ringbtn_top_r_btn = qt.QPushButton(self.ui.widget_22)
    self.show_ringbtn_top_r_btn.setStyleSheet("border:none;background-color:rgba(0,0,0,0);")
    self.show_ringbtn_top_r_btn.setGeometry(qt.QRect(147, 0, 300, 200))
    self.show_ringbtn_top_r_btn.clicked.connect(self.show_ringbtn_r_top_slot)
    self.ringbtn_r_top = RingBtn.MyRingBtn(self.ui.widget_22)
    self.ringbtn_r_top.setGeometry(qt.QRect(170, 0, 300, 300))
    self.ringbtn_r_top.hide()
    #右侧胫骨
    self.show_ringbtn_bottom_r_btn = qt.QPushButton(self.ui.widget_22)
    self.show_ringbtn_bottom_r_btn.setStyleSheet("border:none;background-color:rgba(0,0,0,0);")
    self.show_ringbtn_bottom_r_btn.setGeometry(qt.QRect(147, 310, 300, 200))
    self.show_ringbtn_bottom_r_btn.clicked.connect(self.show_ringbtn_r_bottom_slot)
    self.ringbtn_r_bottom = RingBtn.MyRingBtn(self.ui.widget_22)
    self.ringbtn_r_bottom.setGeometry(qt.QRect(170, 240, 300, 300))
    self.ringbtn_r_bottom.hide()
  #圆环按钮显示
  def show_ringbtn_top_slot(self):
    #左上
    self.ringbtn_top.show()
    self.show_ringbtn_top_btn.hide()
    self.ringbtn_top.Onshow_widgetClicked()
    #左下
    self.ringbtn_bottom.hide()
    self.show_ringbtn_bottom_btn.show()
    self.ringbtn_bottom.status = False
    #右上
    self.ringbtn_r_top.hide()
    self.show_ringbtn_top_r_btn.show()
    self.ringbtn_r_top.status = False
    #右下
    self.ringbtn_r_bottom.hide()
    self.show_ringbtn_bottom_r_btn.show()
    self.ringbtn_r_bottom.status = False
  def show_ringbtn_bottom_slot(self):
    #左上
    self.ringbtn_top.hide()
    self.show_ringbtn_top_btn.show()
    self.ringbtn_top.status = False
    #左下
    self.ringbtn_bottom.show()
    self.show_ringbtn_bottom_btn.hide()
    self.ringbtn_bottom.Onshow_widgetClicked()
    #右上
    self.ringbtn_r_top.hide()
    self.show_ringbtn_top_r_btn.show()
    self.ringbtn_r_top.status = False
    #右下
    self.ringbtn_r_bottom.hide()
    self.show_ringbtn_bottom_r_btn.show()
    self.ringbtn_r_bottom.status = False
  def show_ringbtn_r_top_slot(self):
    #左上
    self.ringbtn_top.hide()
    self.show_ringbtn_top_btn.show()
    self.ringbtn_top.status = False
    #左下
    self.ringbtn_bottom.hide()
    self.show_ringbtn_bottom_btn.show()
    self.ringbtn_bottom.status = False
    #右上
    self.ringbtn_r_top.show()
    self.show_ringbtn_top_r_btn.hide()
    self.ringbtn_r_top.Onshow_widgetClicked()
    #右下
    self.ringbtn_r_bottom.hide()
    self.show_ringbtn_bottom_r_btn.show()
    self.ringbtn_r_bottom.status = False
  def show_ringbtn_r_bottom_slot(self):
    #左上
    self.ringbtn_top.hide()
    self.show_ringbtn_top_btn.show()
    self.ringbtn_top.status = False
    #左下
    self.ringbtn_bottom.hide()
    self.show_ringbtn_bottom_btn.show()
    self.ringbtn_bottom.status = False
    #右上
    self.ringbtn_r_top.hide()
    self.show_ringbtn_top_r_btn.show()
    self.ringbtn_r_top.status = False
    #右下
    self.ringbtn_r_bottom.show()
    self.show_ringbtn_bottom_r_btn.hide()
    self.ringbtn_r_bottom.Onshow_widgetClicked()

  #启用右侧三维视窗鼠标交互
  def view2_can_moving(self):
    if self.ui.pushButton_19.checked:
      #启用交互
      print("启用交互")
      #禁用圆环按钮
      self.ui.pushButton.setChecked(0)
      self.ringbtn_r_top.hide()
      self.show_ringbtn_top_r_btn.hide()
      self.ringbtn_r_bottom.hide()
      self.show_ringbtn_bottom_r_btn.hide()


  #启用右侧三维视窗圆环按钮
  def view2_can_ring(self):
    if self.ui.pushButton.checked:
      #启用圆环按钮
      self.ringbtn_r_top.hide()
      self.show_ringbtn_top_r_btn.show()
      self.ringbtn_r_top.status = False
      self.ringbtn_r_bottom.hide()
      self.show_ringbtn_bottom_r_btn.show()
      self.ringbtn_r_bottom.status = False
      #禁用交互
      print("禁用交互")
      # self.interactorStyle = self.viewWidget2.threeDView().interactorStyle()
      # self.interactorStyle.SetInteractor(None )
      self.ui.pushButton_19.setChecked(0)


  #显示假体
  def guihua_show_jiati(self):
      if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        femurJtName=self.FemurL
      else:
        femurJtName=self.FemurR
      jiati = slicer.util.getNode(femurJtName)

      if self.ui.pushButton_44.checked:
        jiati.SetDisplayVisibility(1)
        self.ChenDian.SetDisplayVisibility(1)
        slicer.util.getNode(self.TibiaJiaTi).SetDisplayVisibility(1)
      else:
        jiati.SetDisplayVisibility(0)
        self.ChenDian.SetDisplayVisibility(0)
        slicer.util.getNode(self.TibiaJiaTi).SetDisplayVisibility(0)

  #显示截骨
  def guihua_show_jiegu(self):
    jinggu_jiegu = slicer.util.getNode("胫骨近端")
    gugu_jiegu = slicer.util.getNode("股骨远端")
    if self.ui.pushButton_45.checked:
      jinggu_jiegu.SetDisplayVisibility(0)
      gugu_jiegu.SetDisplayVisibility(0)
    else:
      jinggu_jiegu.SetDisplayVisibility(1)
      gugu_jiegu.SetDisplayVisibility(1)

  #显示标志点
  def guihua_show_points(self):
    if self.ui.pushButton_46.checked:
      for name in self.all_points:
        slicer.util.getNode(name).SetDisplayVisibility(1)
    else:
      for name in self.all_points:
        slicer.util.getNode(name).SetDisplayVisibility(0)    

  #左侧三维视窗居中
  def leftviewcenter(self):
    self.viewWidget1.threeDView().resetFocalPoint()#居中
    self.viewWidget1.threeDView().lookFromAxis(5)#5正视图  1侧视图
    #放大缩小视图
    view1 = self.viewWidget1.threeDView()
    cameraNode = view1.cameraNode()
    cameraNode.GetCamera().SetPosition(0.00867788456688244, 300.87647608179907, -0.23684020869988087)
    self.viewWidget1.threeDView().resetFocalPoint()#居中
    cameraNode.GetCamera().SetFocalPoint(3,0,20)#左右上下移动
    self.viewWidget1.threeDView().lookFromAxis(5)#5正视图  1侧视图
    
  #右侧三维视窗居中
  def rightviewcenter(self):
    self.viewWidget2.threeDView().resetFocalPoint()
    self.viewWidget2.threeDView().lookFromAxis(1)
    view2 = self.viewWidget2.threeDView()
    cameraNode2 = view2.cameraNode()
    cameraNode2.GetCamera().SetPosition(0.00867788456688244, 300.87647608179907, -0.23684020869988087)
    self.viewWidget2.threeDView().resetFocalPoint()
    cameraNode2.GetCamera().SetFocalPoint(3,0,15)#左右上下移动
    self.viewWidget2.threeDView().lookFromAxis(1)

    

  #模型伸直
  def guihua_shenzhi(self):
    if self.ui.pushButton_51.checked:
      self.ui.pushButton_52.setChecked(0)
      self.ChangeJtStatueToQuxi(0)
      #显示内外翻角
      self.ui.label_61.setText("股骨 内翻/外翻")
      self.ui.label_62.setText("- - -")
      self.ui.label_65.setText("胫骨 内翻/外翻")
      self.ui.label_69.setText("- - -")
      if self.ui.pushButton_45.checked:
        slicer.util.getNode('股骨远端').SetDisplayVisibility(0)
      else:
        slicer.util.getNode('股骨远端').SetDisplayVisibility(1)
    else:
      self.ui.pushButton_51.setChecked(1)
  #模型屈膝
  def guihua_quxi(self):
    if self.ui.pushButton_52.checked:
      self.ui.pushButton_51.setChecked(0)
      self.ChangeJtStatueToQuxi(1)
      self.viewWidget2.threeDView().lookFromAxis(1)#5正视图  1侧视图
      #显示内外旋角
      self.ui.label_61.setText("股骨 内旋/外旋")
      self.ui.label_62.setText("- - -")
      self.ui.label_65.setText("胫骨 内旋/外旋")
      self.ui.label_69.setText("- - -")
      if self.ui.pushButton_45.checked:
        slicer.util.getNode('股骨远端').SetDisplayVisibility(0)
      else:
        slicer.util.getNode('股骨远端').SetDisplayVisibility(1)
    else:
      self.ui.pushButton_52.setChecked(1)

  #文本更新---------------------------------------------------------------
  #股骨内外翻角
  def gugu_neiwaifan_jiao(self,angle):
    self.ui.label_62.setText(f"{round(angle,1)}°")

  #胫骨内外翻角
  def jinggu_neiwaifan_jiao(self,angle):
    self.ui.label_69.setText(f"{round(angle,1)}°")

  #股骨内外旋角
  def gugu_neiwaixuan_jiao(self,angle):
    self.ui.label_62.setText(f"{round(angle,1)}°")

  #胫骨内外旋角
  def jinggu_neiwaixuan_jiao(self,angle):
    self.ui.label_69.setText(f"{round(angle,1)}°")

  #股骨远端外侧截骨量A2
  def gugu_waice_yuanduan(self,value):
    self.ui.label_6.setText(f"{round(value,1)}mm")

  #股骨后髁外侧截骨量C2
  def gugu_waice_houke(self,value):
    self.ui.label_8.setText(f"{round(value,1)}mm")

  #胫骨近端外侧截骨量A3
  def jinggu_waice_jinduan(self,value):
    self.ui.label_11.setText(f"{round(value,1)}mm")


  #股骨远端内侧截骨量B2
  def gugu_neice_yuanduan(self,value):
    self.ui.label_28.setText(f"{round(value,1)}mm")

  #股骨后髁内侧截骨量C3
  def gugu_neice_houke(self,value):
    self.ui.label_39.setText(f"{round(value,1)}mm")

  #胫骨近端内侧截骨量B3
  def jinggu_neice_jinduan(self,value):
    self.ui.label_60.setText(f"{round(value,1)}mm")

#---------------------------------------------------
  #笔针厚度
  def bizhen_houdu(self,value):
    self.ui.label_77.setText(f"{round(value,1)}mm")
    self.ui.label_71.setText(f"{round(value,1)}mm")

  #股骨倾角
  def gugu_qingjiao(self,value):
    self.ui.label_73.setText(f"{round(value,1)}°")

  #胫骨后倾角
  def jinggu_qing_jiao(self,value):
    self.ui.label_75.setText(f"{round(value,1)}°")

  #伸直内侧间隙A1
  def shenzhi_neice_jianxi(self,value):
    self.stylusset.space_size.setPlainText(f"{round(value,1)}mm")

  #伸直内侧截骨A10
  def shenzhi_neice_jiegu(self,value):
    self.stylusset.cuts_top.setPlainText(f"{round(value,1)}mm")

  #伸直内侧理论A11
  def shenzhi_neice_lilun(self,value):
    self.stylusset.cuts_bottom.setPlainText(f"{round(value,1)}mm")

  #屈膝内侧理论A12
  def quxi_neice_lilun(self,value):
    self.stylusset.flex.setPlainText(f"屈膝. {round(value,1)}mm")

  #伸直外侧间隙B1
  def shenzhi_waice_jianxi(self,value):
    self.stylusset.space_size_r.setPlainText(f"{round(value,1)}mm")

  #伸直外侧截骨B10
  def shenzhi_waice_jiegu(self,value):
    self.stylusset.cuts_top_r.setPlainText(f"{round(value,1)}mm")

  #伸直外侧理论B11
  def shenzhi_waice_lilun(self,value):
    self.stylusset.cuts_bottom_r.setPlainText(f"{round(value,1)}mm")

  #屈膝外侧理论B12
  def quxi_waice_lilun(self,value):
    self.stylusset.flex_r.setPlainText(f"屈膝. {round(value,1)}mm")

  #屈膝角
  def shenzhi_quxi(self,value):
    self.stylusset.extension_jiaodu.setPlainText(f"{round(value,1)}°")

  #胫股间距C1
  def jing_gu_jianju(self,value):
    self.stylusset.component_size.setPlainText(f"{round(value,1)}mm")

  #显示韧带平衡ui
  def show_rendai_pingheng(self):
    if self.ui.pushButton_48.checked:
      self.ui.stackedWidget_4.setCurrentIndex(0)
    else:
      self.ui.stackedWidget_4.setCurrentIndex(1)

  #手术规划信号槽连接
  def planning_btn_connect(self):
    #韧带平衡按钮
    self.ui.pushButton_48.clicked.connect(self.show_rendai_pingheng)
    #圆环按钮-左侧-股骨
    self.ringbtn_top.btn_left.clicked.connect(lambda x:self.Adjust_femur_position(11))
    self.ringbtn_top.btn_right.clicked.connect(lambda x:self.Adjust_femur_position(12))
    self.ringbtn_top.btn_top.clicked.connect(lambda x:self.Adjust_femur_position(13))
    self.ringbtn_top.btn_bottom.clicked.connect(lambda x:self.Adjust_femur_position(14))
    self.ringbtn_top.btn_arrow_right.clicked.connect(lambda x:self.Adjust_femur_position(15))
    self.ringbtn_top.btn_arrow_left.clicked.connect(lambda x:self.Adjust_femur_position(16))
    #圆环按钮-左侧-胫骨
    self.ringbtn_bottom.btn_left.clicked.connect(lambda x:self.Adjust_Tibia_position(11))
    self.ringbtn_bottom.btn_right.clicked.connect(lambda x:self.Adjust_Tibia_position(12))
    self.ringbtn_bottom.btn_top.clicked.connect(lambda x:self.Adjust_Tibia_position(13))
    self.ringbtn_bottom.btn_bottom.clicked.connect(lambda x:self.Adjust_Tibia_position(14))
    self.ringbtn_bottom.btn_arrow_right.clicked.connect(lambda x:self.Adjust_Tibia_position(15))
    self.ringbtn_bottom.btn_arrow_left.clicked.connect(lambda x:self.Adjust_Tibia_position(16))
    #圆环按钮-右侧-股骨
    self.ringbtn_r_top.btn_left.clicked.connect(lambda x:self.Adjust_femur_position(21))
    self.ringbtn_r_top.btn_right.clicked.connect(lambda x:self.Adjust_femur_position(22))
    self.ringbtn_r_top.btn_top.clicked.connect(lambda x:self.Adjust_femur_position(23))
    self.ringbtn_r_top.btn_bottom.clicked.connect(lambda x:self.Adjust_femur_position(24))
    self.ringbtn_r_top.btn_arrow_right.clicked.connect(lambda x:self.Adjust_femur_position(25))
    self.ringbtn_r_top.btn_arrow_left.clicked.connect(lambda x:self.Adjust_femur_position(26))
    #圆环按钮-右侧-胫骨
    self.ringbtn_r_bottom.btn_left.clicked.connect(lambda x:self.Adjust_Tibia_position(21))
    self.ringbtn_r_bottom.btn_right.clicked.connect(lambda x:self.Adjust_Tibia_position(22))
    self.ringbtn_r_bottom.btn_top.clicked.connect(lambda x:self.Adjust_Tibia_position(23))
    self.ringbtn_r_bottom.btn_bottom.clicked.connect(lambda x:self.Adjust_Tibia_position(24))
    self.ringbtn_r_bottom.btn_arrow_right.clicked.connect(lambda x:self.Adjust_Tibia_position(25))
    self.ringbtn_r_bottom.btn_arrow_left.clicked.connect(lambda x:self.Adjust_Tibia_position(26))
    #伸直屈膝按钮
    self.ui.pushButton_51.clicked.connect(self.guihua_shenzhi)
    self.ui.pushButton_52.clicked.connect(self.guihua_quxi)
    #显示假体按钮
    self.ui.pushButton_44.clicked.connect(self.guihua_show_jiati)
    #显示截骨按钮
    self.ui.pushButton_45.clicked.connect(self.guihua_show_jiegu)
    #显示标志点按钮
    self.ui.pushButton_46.clicked.connect(self.guihua_show_points)
    #启用三维视窗交互按钮
    self.ui.pushButton_19.clicked.connect(self.view2_can_moving)
    #启用圆环按钮
    self.ui.pushButton.clicked.connect(self.view2_can_ring)

  #圆环按钮调整模型位置
  #股骨
  def Adjust_femur_position(self,x):
    if x<20:
      if self.ui.pushButton_51.checked:
        if x == 11:#左移动
          slicer.modules.popup.widgetRepresentation().self().onxMoveButton2()
        elif x == 12:#右移动
          slicer.modules.popup.widgetRepresentation().self().onxMoveButton1()
        elif x == 13:#上移动
          slicer.modules.popup.widgetRepresentation().self().onzMoveButton2()
        elif x == 14:#下移动
          slicer.modules.popup.widgetRepresentation().self().onzMoveButton1()
        elif x == 15:#右旋转
          slicer.modules.popup.widgetRepresentation().self().onySpinButton1()
        else:#左旋转
          slicer.modules.popup.widgetRepresentation().self().onySpinButton2()
      else:
        if x == 11:#左移动
          slicer.modules.popup.widgetRepresentation().self().onxMoveButton2()
        elif x == 12:#右移动
          slicer.modules.popup.widgetRepresentation().self().onxMoveButton1()
        elif x == 13:#上移动
          slicer.modules.popup.widgetRepresentation().self().onyMoveButton2()
        elif x == 14:#下移动
          slicer.modules.popup.widgetRepresentation().self().onyMoveButton1()
        elif x == 15:#右旋转
          slicer.modules.popup.widgetRepresentation().self().onzSpinButton1()
        else:#左旋转
          slicer.modules.popup.widgetRepresentation().self().onzSpinButton2()
    else:
      if self.ui.pushButton_51.checked:
        if x == 21:#左移动
          slicer.modules.popup.widgetRepresentation().self().onyMoveButton1()
        elif x == 22:#右移动
          slicer.modules.popup.widgetRepresentation().self().onyMoveButton2()
        elif x == 23:#上移动
          slicer.modules.popup.widgetRepresentation().self().onzMoveButton2()
        elif x == 24:#下移动
          slicer.modules.popup.widgetRepresentation().self().onzMoveButton1()
        elif x == 25:#右旋转
          slicer.modules.popup.widgetRepresentation().self().onxSpinButton1()
        else:#左旋转
          slicer.modules.popup.widgetRepresentation().self().onxSpinButton2()
      else:
        if x == 21:#左移动
          slicer.modules.popup.widgetRepresentation().self().onzMoveButton2()
        elif x == 22:#右移动
          slicer.modules.popup.widgetRepresentation().self().onzMoveButton1()
        elif x == 23:#上移动
          slicer.modules.popup.widgetRepresentation().self().onyMoveButton2()
        elif x == 24:#下移动
          slicer.modules.popup.widgetRepresentation().self().onyMoveButton1()
        elif x == 25:#右旋转
          slicer.modules.popup.widgetRepresentation().self().onxSpinButton1()
        else:#左旋转
          slicer.modules.popup.widgetRepresentation().self().onxSpinButton2()

  #胫骨
  def Adjust_Tibia_position(self,x):
    if x<20:
      if x == 11:#左移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onxMoveButton2()
      elif x == 12:#右移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onxMoveButton1()
      elif x == 13:#上移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onzMoveButton2()
      elif x == 14:#下移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onzMoveButton1()
      elif x == 15:#右旋转
        slicer.modules.tibiapopup.widgetRepresentation().self().onySpinButton1()
      else:#左旋转
        slicer.modules.tibiapopup.widgetRepresentation().self().onySpinButton2()
    else:
      if x == 21:#左移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onyMoveButton1()
      elif x == 22:#右移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onyMoveButton2()
      elif x == 23:#上移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onzMoveButton2()
      elif x == 24:#下移动
        slicer.modules.tibiapopup.widgetRepresentation().self().onzMoveButton1()
      elif x == 25:#右旋转
        slicer.modules.tibiapopup.widgetRepresentation().self().onxSpinButton1()
      else:#左旋转
        slicer.modules.tibiapopup.widgetRepresentation().self().onxSpinButton2()

  def OnAdjustReset(self):
    Trans = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    FemurTransform = slicer.util.getNode("变换_股骨调整")
    FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Trans))
    TibiaTransform = slicer.util.getNode("变换_胫骨调整")
    TibiaTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Trans))
    slicer.modules.popup.widgetRepresentation().self().onConfirm()
    slicer.modules.tibiapopup.widgetRepresentation().self().onConfirm()


#----------------------手术规划（结束）-------------------------------------------------

#-------------------------切割（开始）-----------------------------------------------
  #切割界面动态UI
  def cut_Animationui(self):
    #页4-1
    self.flipcorner_one = Flipcorner_one.Flipcorner_one()
    layout = qt.QHBoxLayout(self.ui.widget_60)
    layout.addWidget(self.flipcorner_one)

    self.flipcorner_0 = MyFlipcorner.MyFlipcorner() #记录角度ui
    self.flipcorner_0.graphicsview.setSceneRect(qt.QRectF(0,-40,1,1))
    self.flipcorner_0.graphicsview.scale(1.6,1.3)
    lay = qt.QHBoxLayout(self.ui.widget_58)
    lay.addWidget(self.flipcorner_0)
    #页4-2
    self.leg_rotation_cut = LegRotation.LegRotation() #腿部旋转ui
    self.bonegap = MyBoneGap.MyBoneGap()
    layout = qt.QHBoxLayout(self.ui.widget_52)
    layout.addWidget(self.leg_rotation_cut)
    layout = qt.QHBoxLayout(self.ui.widget_53)
    layout.addWidget(self.bonegap)
  #信号槽链接
  def cut_connect(self):
    self.ui.stackedWidget_3.setCurrentIndex(0)
    self.ui.stackedWidget_6.setCurrentIndex(0)
    self.ui.stackedWidget_7.setCurrentIndex(0)
    self.queren_label()
    self.bones_pos()#文本初始位置
    self.gugu_bone_show(False)
    self.jinggu_bone_show(False)
    self.gugu_bone2_show(False)
    #设置背景图片
    self.stacklayout = qt.QStackedLayout(self.ui.widget_40)
    self.cut_bg_label = qt.QLabel(self.ui.widget_40)
    self.cut_bg_label.setStyleSheet("background-color: rgb(46, 76, 112);")
    # self.change_cut_background("cut_1_1")
    self.stacklayout.addWidget(self.cut_bg_label)
    self.stacklayout.addWidget(self.ui.stackedWidget_3)
    self.stacklayout.setCurrentIndex(1)
    self.stacklayout.setStackingMode(1)
    #设置label图片
    self.ui.label_86.setPixmap(qt.QPixmap(self.newImgPath+"/截图/踏板.png").scaled(self.ui.label_86.width,self.ui.label_86.width,qt.Qt.KeepAspectRatio))
    # self.ui.label_86.setScaledContents(True)
    self.ui.label_92.setPixmap(qt.QPixmap(self.newImgPath+"/截图/踏板.png").scaled(self.ui.label_92.height,self.ui.label_92.height,qt.Qt.KeepAspectRatio))
    # self.ui.label_92.setScaledContents(True)
    self.ui.label_97.setPixmap(qt.QPixmap(self.newImgPath+"/截图/踏板.png").scaled(self.ui.label_97.width,self.ui.label_97.width,qt.Qt.KeepAspectRatio))
    self.ui.label_98.setPixmap(qt.QPixmap(self.newImgPath+"/截图/踏板.png").scaled(self.ui.label_98.width,self.ui.label_98.width,qt.Qt.KeepAspectRatio))
    # self.ui.label_97.setScaledContents(True)
    self.ui.label_104.setPixmap(qt.QPixmap(self.newImgPath+"/截图/踏板.png").scaled(self.ui.label_104.height,self.ui.label_104.height,qt.Qt.KeepAspectRatio))
    self.ui.label_110.setPixmap(qt.QPixmap(self.newImgPath+"/截图/yanzheng.png").scaled(self.ui.label_97.width,self.ui.label_97.width,qt.Qt.KeepAspectRatio))
    
    #第一页页面切换
    self.change_cut_label_96("cut_1_1")
    self.ui.pushButton_40.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_6))
    self.ui.pushButton_40.clicked.connect(lambda:self.change_cut_label_96("cut_1_2"))
    self.ui.pushButton_41.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_6))
    self.ui.pushButton_41.clicked.connect(lambda:self.change_cut_label_96("cut_1_3"))
    self.ui.pushButton_42.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_6))
    self.ui.pushButton_42.clicked.connect(lambda:self.change_cut_label_96("checked"))
    self.ui.pushButton_43.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_3))
    self.ui.pushButton_43.clicked.connect(lambda:self.change_cut_background("move2cutplane"))
    #第二页页面切换
    self.ui.pushButton_54.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_7))
    self.ui.pushButton_55.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_7))
    self.ui.pushButton_55.clicked.connect(lambda:self.change_cut_background("move2bone"))
    self.ui.pushButton_56.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_7))
    self.ui.pushButton_56.clicked.connect(lambda:self.change_cut_background("bone1"))
    self.ui.pushButton_56.clicked.connect(lambda:self.gugu_bone_show(True))
    self.ui.pushButton_56.clicked.connect(self.SetGuihuaValue)
    self.ui.pushButton_58.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_7))
    self.ui.pushButton_60.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_7))
    self.ui.pushButton_60.clicked.connect(lambda:self.change_cut_background("bone2move"))
    self.ui.pushButton_60.clicked.connect(lambda:self.gugu_bone_show(False))
    self.ui.pushButton_62.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_7))
    self.ui.pushButton_62.clicked.connect(lambda:self.change_cut_background("move2cutplane"))
    self.ui.pushButton_63.clicked.connect(lambda:self.ui.stackedWidget_3.setCurrentIndex(0))
    self.ui.pushButton_63.clicked.connect(lambda:self.ui.stackedWidget_6.setCurrentIndex(3))
    self.ui.pushButton_49.clicked.connect(lambda:self.ui.stackedWidget_3.setCurrentIndex(2))
    self.ui.pushButton_49.clicked.connect(lambda:self.change_cut_background("move2cutplane"))
    #第三页
    self.ui.pushButton_64.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_8))
    self.ui.pushButton_65.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_8))
    self.ui.pushButton_65.clicked.connect(lambda:self.change_cut_background("move2bone2"))
    self.ui.pushButton_66.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_8))
    self.ui.pushButton_66.clicked.connect(lambda:self.change_cut_background("bone2"))
    self.ui.pushButton_66.clicked.connect(lambda:self.jinggu_bone_show(True))
    self.ui.pushButton_68.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_8))
    self.ui.pushButton_70.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_8))
    self.ui.pushButton_70.clicked.connect(lambda:self.change_cut_background("bone2move2"))
    self.ui.pushButton_70.clicked.connect(lambda:self.jinggu_bone_show(False))
    self.ui.pushButton_72.clicked.connect(lambda:self.ui.stackedWidget_8.setCurrentIndex(7))
    self.ui.pushButton_72.clicked.connect(lambda:self.change_cut_background("bone3"))
    self.ui.pushButton_72.clicked.connect(lambda:self.gugu_bone2_show(True))
    self.ui.pushButton_72.clicked.connect(lambda:self.jinggu_bone_show(True))
    self.ui.pushButton_72.clicked.connect(self.jinggu_bone_pos_changed)
    # self.ui.pushButton_72.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_8))
    # self.ui.pushButton_72.clicked.connect(lambda:self.change_cut_background("move2cutplane"))
    # self.ui.pushButton_73.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_3))
    self.ui.pushButton_75.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_8))
    self.ui.pushButton_74.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_3))
    self.ui.pushButton_74.clicked.connect(self.clearrrr)
    self.ui.pushButton_74.clicked.connect(lambda:self.gugu_bone2_show(False))
    self.ui.pushButton_74.clicked.connect(lambda:self.jinggu_bone_show(False))
    #第四页
    self.ui.pushButton_25.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_10))
    self.ui.pushButton_28.clicked.connect(lambda:self.PreparatChangeDownPage(self.ui.stackedWidget_10))
    self.ui.pushButton_28.clicked.connect(lambda:self.label_115_bg("okokok"))

  def change_cut_background(self,img):
    self.cut_bg_label.setPixmap(qt.QPixmap(self.newImgPath+"/截图/"+img+".png"))
    self.cut_bg_label.setScaledContents(True)
  
  def clearrrr(self):
    self.cut_bg_label.clear()

  def change_cut_label_96(self,img):
    self.ui.label_96.setPixmap(qt.QPixmap(self.newImgPath+"/截图/"+img+".png"))
    self.ui.label_96.setScaledContents(True)
  
  def label_115_bg(self,img):
    self.ui.label_115.setPixmap(qt.QPixmap(self.newImgPath+"/截图/"+img+".png"))
    self.ui.label_115.setScaledContents(True)   
  
  def queren_label(self):
    self.ui.label_126.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_126.setScaledContents(True)
    self.ui.label_167.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))#.scaled(self.ui.label_167.width,self.ui.label_167.width))
    self.ui.label_167.setScaledContents(True) 
    self.ui.label_162.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))#.scaled(self.ui.label_162.width,self.ui.label_162.width))
    self.ui.label_162.setScaledContents(True) 
    self.ui.label_132.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))#.scaled(self.ui.label_132.width,self.ui.label_132.width))
    self.ui.label_132.setScaledContents(True)

    self.ui.label_142.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_142.setScaledContents(True)
    self.ui.label_147.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_147.setScaledContents(True) 
    self.ui.label_152.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_152.setScaledContents(True) 
    self.ui.label_157.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_157.setScaledContents(True) 
    self.ui.label_172.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_172.setScaledContents(True) 
    self.ui.label_182.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_182.setScaledContents(True) 
    self.ui.label_192.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_192.setScaledContents(True) 
    self.ui.label_177.setPixmap(qt.QPixmap(self.newImgPath+"/截图/确认.png"))
    self.ui.label_177.setScaledContents(True)

  def gugu_bone_show(self,show):
    if show:
      self.ui.widget_47.show()
      self.ui.widget_77.show()
      self.ui.widget_76.show()
      self.ui.widget_70.show()
    else:
      self.ui.widget_47.hide()
      self.ui.widget_77.hide()
      self.ui.widget_76.hide()
      self.ui.widget_70.hide()     

  def jinggu_bone_show(self,show):
    if show:
      self.ui.widget_72.show()
      self.ui.widget_73.show()
      self.ui.widget_74.show()
      self.ui.widget_75.show()
    else:
      self.ui.widget_72.hide()
      self.ui.widget_73.hide()
      self.ui.widget_74.hide()
      self.ui.widget_75.hide()
  def jinggu_bone_pos_changed(self):
      self.ui.widget_72.setGeometry(30,320,218,131)
      self.ui.widget_73.setGeometry(300,320,218,131)
      self.ui.widget_74.setGeometry(520,320,218,131)
      self.ui.widget_75.setGeometry(180,420,218,131)
  
  def gugu_bone2_show(self,show):
    if show:
      self.ui.widget_78.show()
      self.ui.widget_80.show()
      self.ui.widget_82.show()
      self.ui.widget_79.show() 
    else:
      self.ui.widget_78.hide()
      self.ui.widget_80.hide()
      self.ui.widget_82.hide()
      self.ui.widget_79.hide()

  def bones_pos(self):
    #股骨
    self.ui.widget_47.setGeometry(220,100,218,131)
    self.ui.widget_77.setGeometry(650,180,218,131)
    self.ui.widget_76.setGeometry(50,320,218,131)
    self.ui.widget_70.setGeometry(350,320,218,131)
    #胫骨
    self.ui.widget_73.setGeometry(400,48,218,131)
    self.ui.widget_74.setGeometry(650,48,218,131)
    self.ui.widget_75.setGeometry(230,230,218,131)

    self.ui.widget_78.setGeometry(190,50,218,131)
    self.ui.widget_80.setGeometry(520,80,218,131)
    self.ui.widget_82.setGeometry(30,160,218,131)
    self.ui.widget_79.setGeometry(300,160,218,131)

  #设置角度值
  def cut_angle_changed(self,label,value):
    label.setText(f"{round(value,1)}°")

  #设置长度值
  def cut_lenth_changed(self,label,value):
    label.setText(f"{round(value,1)}mm")

  #显示规划数据
  def SetGuihuaValue(self):
    #股骨
    self.ui.label_125.setText(self.ui.label_62.text)
    self.ui.label_171.setText(self.ui.label_73.text)
    self.ui.label_166.setText(self.ui.label_6.text)
    self.ui.label_136.setText(self.ui.label_28.text)
    #股骨+胫骨
    self.ui.label_146.setText(self.ui.label_11.text)
    self.ui.label_151.setText(self.ui.label_60.text)
    self.ui.label_156.setText(self.ui.label_75.text)
    self.ui.label_161.setText(self.ui.label_69.text)

    self.ui.label_176.setText(self.ui.label_62.text)
    self.ui.label_186.setText(self.ui.label_73.text)
    self.ui.label_196.setText(self.ui.label_6.text)
    self.ui.label_181.setText(self.ui.label_28.text)

#-------------------------切割（结束）-----------------------------------------------

    # #------------------------股骨规划------------------------------------------------
    # self.ui.Parameter.connect('clicked(bool)', self.onParameter)#骨骼参数按钮
    # self.ui.Adjustment.connect('clicked(bool)', self.onAdjustment)#截骨调整按钮
    # self.ui.ViewChoose.connect('clicked(bool)', self.onViewSelect)#视图选择按钮
    # self.ui.Reset.connect('clicked(bool)', self.onReset)#重置按钮
    # self.ui.ForceLine.connect('clicked(bool)',self.onForceLine)#显示力线
    # self.ui.ForceConfirm.connect('clicked(bool)',self.onForceConfirm)#力线确认

    # #添加logo图片
    # Logo = slicer.util.findChild(slicer.util.mainWindow(),"Logo")
    # pixmap = qt.QPixmap(self.iconsPath+'/Logo.png')
    # Logo.setPixmap(pixmap)
  
    # self.ui.FemurSwitch.setIcon(qt.QIcon(self.iconsPath+'/FemurSwitch.png'))
    # self.ui.TibiaSwitch.setIcon(qt.QIcon(self.iconsPath+'/TibiaSwitch.png'))

    # self.ms = MySignals()
    # # 关联处理该信号的函数
    # self.ms.labeltxt.connect(self.handleCalc_do)

    # self.ifsend03=0

    # #------------------------胫骨规划------------------------------------------------
    # #self.ui.Parameter2.connect('clicked(bool)', self.onParameter2)#骨骼参数按钮
    # self.ui.Parameter2.connect('clicked(bool)', self.onParameter)
    # self.ui.Adjustment2.connect('clicked(bool)', self.onAdjustment2)#截骨调整按钮
    # #self.ui.ViewChoose2.connect('clicked(bool)', self.onTibiaViewSelect)#视图选择按钮
    # self.ui.ViewChoose2.connect('clicked(bool)', self.onViewSelect)#视图选择按钮
    # self.ui.ReSet2.connect('clicked(bool)', self.onReset)#重置按钮
    # self.ui.ForceLine2.connect('clicked(bool)',self.onForceLine)#显示力线
    # #--------------------------报告--------------------------------------------------
    # self.ui.JieTu.connect('clicked(bool)', self.onJieTu)#调直按钮
    # self.ui.CTReport.connect('clicked(bool)', self.onCTReport)#CT按钮
    # self.ui.MRIReport.connect('clicked(bool)', self.onMRIReport)#MRI按钮
    # self.ui.path.setText('D:/Data')
    # self.ui.pathButton.connect('clicked(bool)', self.onPath)
    # self.ui.ConfirmReport.connect('clicked(bool)', self.onConfirmReport)
    # #-------------------------head1-------------------------------------------------
    # self.ui.JiaTiButton.connect('clicked(bool)', self.onJiaTiButton)#假体按钮
    # self.ui.BoneButton.connect('clicked(bool)', self.onBoneButton)#截骨面按钮
    # self.ui.MarkerButton.connect('clicked(bool)', self.onMarkerButton)#标志点按钮
    # self.ui.TransparentButton.connect('clicked(bool)', self.onTransparentButton)#透明显示按钮
    # self.ui.FemurSwitch.connect('clicked(bool)',self.onFemurSwitch)#切换到股骨截骨调整
    # self.ui.TibiaSwitch.connect('clicked(bool)',self.onTibiaSwitch)#切换到胫骨截骨调整
    # self.ui.FemurR.connect('currentIndexChanged(int)',self.onFemurR)#股骨假体右侧ComboBox
    # self.ui.FemurL.connect('currentIndexChanged(int)',self.onFemurL)#股骨假体左侧ComboBox
    # self.ui.TibiaJiaTi.connect('currentIndexChanged(int)',self.onTibiaJiaTi)#胫骨假体ComboBox
    # self.ui.TibiaShowHide.connect('clicked(bool)',self.onTibiaShowHide)#胫骨近端是否显示
    # self.ui.FemurShowHide.connect('clicked(bool)',self.onFemurShowHide)#股骨远端是否显示
    # #-----------------------------Graph功能-------------------------------------------
    # self.ui.PopupImage.connect('clicked(bool)',self.PopupGraph)#弹出图像
    # self.ui.ClearImage.connect('clicked(bool)',self.ClearGraph)#清空图像
    # self.ui.DrawImage.connect('clicked(bool)',self.DrawGraph)#绘制图像
    # self.ui.RecordImage.connect('clicked(bool)',self.RecordGraph)#记录图像

    #======================================================================================
    #------------------------------导航----------------------------------------
    # self.ui.NavigationSwitch.connect('clicked(bool)',self.onNavigationSwitch)#导航显示切换
    # #工具校准
    # self.ui.DriveJZ.connect('clicked(bool)',self.onDriveJZ)#电机校准按钮    
    # self.ui.FemurQG.connect('clicked(bool)',self.onFemurQG)#股骨切割按钮
    # self.ui.TibiaQG.connect('clicked(bool)',self.onTibiaQG)#胫骨切割按钮

    # #self.ui.InitDJ.connect('clicked(bool)',self.onInit)#初始化计算角度
    # #切割
    # self.ui.FirstQG.connect('clicked(bool)',self.onFirstQG)#第一刀
    # self.ui.SecondQG.connect('clicked(bool)',self.onSecondQG)
    # self.ui.ThirdQG.connect('clicked(bool)',self.onThirdQG)
    # self.ui.FourthQG.connect('clicked(bool)', self.onFourthQG)
    # self.ui.FifthQG.connect('clicked(bool)',self.onFifthQG)
    # self.ui.QGReSet.connect('clicked(bool)',self.onQGReSet)
    # #切割预览
    # self.ui.FirstPreview.connect('clicked(bool)', self.onFirstPreview)
    # self.ui.SecondPreview.connect('clicked(bool)', self.onSecondPreview)
    # self.ui.ThirdPreview.connect('clicked(bool)', self.onThirdPreview)
    # self.ui.FourthPreview.connect('clicked(bool)', self.onFourthPreview)
    # self.ui.FifthPreview.connect('clicked(bool)', self.onFifthPreview)
    # self.ui.PreviewReSet.connect('clicked(bool)', self.onPreviewReSet)
  #---------------前进后退----------------------------------------------- 
  def onForwardToolButton(self):
    #self.ui.ForwardToolButton.setEnabled(False)
    if self.currentModel == 5:
      return
    
    self.currentModel += 1
    if self.currentModel == 4:
      self.currentModel += 1

    self.WidgetShow(self.currentModel)

  def WidgetShow(self,index):
    # try:
    #   for i in range (0,len(self.ui.GraphImage.children())):
    #     a = self.ui.GraphImage.children()[-1]
    #     try:
    #       a.clear()
    #     except Exception as e:
    #       print("删除GraphImage clear:",e)
    #     try:
    #       a.close()
    #     except Exception as e:
    #       print("删除GraphImage close:",e)
    #     try:
    #       a.deleteLater()
    #     except Exception as e:
    #       print("删除GraphImage deleteLater:",e)
    # except Exception as e:
    #   print("删除GraphImage:",e)


    # self.ui.PopupWidget.setVisible(False)
    # self.ui.head1.setVisible(False)
    # self.ui.OperationPlanWidget.setVisible(False)#手术规划每部分小界面
    # self.ui.NavigationWidget.setVisible(False)
    # self.ui.Graph.setVisible(False)
    # self.ui.InitWidget.setVisible(0)
    
    # for i in range(0,len(self.WidgetList)):
    #   self.WidgetList[i].setVisible(False)
    # self.WidgetList[index].setVisible(True)
    # self.ui.BackToolButton.setToolTip(self.LabelList[index])
    # self.ui.ModuleName.setText(self.LabelList[index+1])
    # self.ui.ForwardToolButton.setToolTip(self.LabelList[index+2])
    
    # if index == 0:#初始化
    #   for i in range(0,len(self.noimageWidget.findChildren("QLabel"))):
    #     self.noimageWidget.findChildren("QLabel")[-1].delete()
      
    #   self.FourImage(True)

    if index == 0:#系统准备
      # self.FourImage(False)
      for i in range(0,len(self.noimageWidget.findChildren("QLabel"))):
        self.noimageWidget.findChildren("QLabel")[-1].delete()
      # self.ui.powerOnButton.click()
      self.PngLabel = qt.QLabel(self.noimageWidget)
      self.PngLabel.resize(self.noimageWidget.width,self.noimageWidget.height)
      self.PngLabel.setScaledContents(True)
      self.PngLabel.setStyleSheet("QLabel{background-color:transparent;}")
      self.pixmap = qt.QPixmap(self.iconsPath+'/background.png')        
      self.PngLabel.setPixmap(self.pixmap)   
      self.PngLabel.show()
      # self.ui.ForwardToolButton.setEnabled(True)

    if index == 1:#股骨配准
      try:
        self.lay_w26.removeWidget(self.ui.widget_25)
      except:
        pass
      self.lay_w27.addWidget(self.ui.widget_25)#widget_25
      # self.ui.tibiaPointWidget.setVisible(False)
      self.ui.femurPointWidget.setVisible(True)
      self.EnterSet()
      self.ui.femurWidget2.setVisible(True)
      self.onFemurRadioButton()
      self.FemurOrTibia()
      s1 = 0
      s2 = 2
      s3 = 0
      s4 = 0
      s5 = 1
      # 股骨或者胫骨图片
      s6 = 1
      s7 = 0
      s8 = '0@\n'
      # self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
      # print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
    if index == 2: #胫骨配准
      try:
        self.lay_w27.removeWidget(self.ui.widget_25)
      except:
        pass
      self.lay_w26.addWidget(self.ui.widget_25)#widget_25

      # self.ui.femurPointWidget.setVisible(False)
      self.ui.tibiaPointWidget.setVisible(True)
      self.EnterSet()
      self.onTibiaRadioButton()
      self.FemurOrTibia()
      s1 = 0
      s2 = 2
      s3 = 0  
      s4 = 1
      s5 = 1
      s6 = 1
      s7 = 0
      s8 = '0@\n'
      # self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
      # print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
    if index == 3:#股骨规划
      s1 = 0
      s2 = 3
      s3 = 0  
      s4 = 0
      s5 = 0
      s6 = 0
      s7 = 0
      s8 = '0@\n'
      self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
      print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
      print("手术规划3")
      #self.FemurButtonChecked(None) 
      #self.buildPointsInFemur() 
      # for i in range (0,len(self.noimageWidget.findChildren('QLabel'))):
      #   self.noimageWidget.findChildren('QLabel')[-1].delete()
    if index == 4:#胫骨规划
      s1 = 0
      s2 = 3
      s3 = 0  
      s4 = 1
      s5 = 0
      s6 = 0
      s7 = 0
      s8 = '0@\n'
      self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
      print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
      # self.HidePart()
      # self.TibiaButtonChecked(None)
      # self.ShowNode('Tibia')
    if index == 5:#导航
      s1 = 0
      s2 = 3
      s3 = 1  
      s4 = 2
      s5 = 0
      s6 = 0
      s7 = 0
      s8 = '0@\n'
      self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
      print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
      # try:
      #   try:
      #     self.hideInformation()
      #   except Exception as e:
      #     print(e)
      #   self.HideAll()
      #   self.HidePart()
      #   self.ShowNode('股骨切割')
      #   self.jiatiload.SetDisplayVisibility(True)
      #   self.ShowNode('胫骨切割')
      #   self.TibiaJiaTiload.SetDisplayVisibility(True)
      #   self.Camera1(self.view1)
      #   self.Camera2(self.view2)
      #   self.Camera3(self.view3)
      #   slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourOverFourView)
      #   view4=slicer.app.layoutManager().threeDWidget('View4').threeDView()
      #   self.TCamera3(view4)
      #   self.loadChenDian()
      #   self.showHide()
      # except:
      #     pass
      for i in range (0,len(self.noimageWidget.findChildren('QLabel'))):
        self.noimageWidget.findChildren('QLabel')[-1].delete()
      self.ThreeDViewAndImageWidget(0)
      slicer.modules.noimageoperationimage.widgetRepresentation().hide()
      slicer.modules.viewselect.widgetRepresentation().hide()
      self.SwitchState = 1
      # self.ui.NavigationToolWidget.setVisible(False)
      djoperationWidget = slicer.modules.djoperation.widgetRepresentation()
      # djoperationWidget.setParent(self.ui.PopupWidget)
      # layout = qt.QHBoxLayout(self.ui.PopupWidget)
      layout.addWidget(djoperationWidget)
      # self.ui.PopupWidget.setLayout(layout)
      # self.ui.PopupWidget.setVisible(True)
      djoperationWidget.resize(420,800)
      djoperationWidget.self().ui.DJOperationWidget.setVisible(0)
      djoperationWidget.show()
      djoperationWidget.self().client = self.client
      djoperationWidget.self().jiatiload = self.jiatiload
      self.DeleteAllNode()

  def onBackToolButton(self):
    if self.currentModel == 0:
      return
    self.currentModel -= 1
    if self.currentModel == 4:
      self.currentModel -=1
    self.WidgetShow(self.currentModel)

  def handleCalc_do1(self,buf):
    buf = buf.strip('@').strip(',')
    buf_list = buf.split('@')
    for i in range(len(buf_list)):
      buf_list1 = buf_list[i].strip(',').split(',')
      if len(buf_list1) == 17:
        name = buf_list1[0]
        buf_list1.pop(0)
        trans = np.zeros([4, 4])
        for i in range(4):
          for j in range(4):
            trans[i][j] = buf_list1[i * 4 + j]
        self.handleData1(name,trans)
        print(name)

  def dealigt(self,asd=None,asdasd=None):
    # 创建客户端套接字
    sk = socket.socket()
    # 尝试连接服务器
    sk.connect(('192.168.3.99', 8898))
    while True:
      # 信息接收
      ret = sk.recv(10240)
      ret = ret.decode()
      # print(ret)
      self.handleCalc_do1(ret)
      time.sleep(0.014)

  def handleData1(self, name, trans):
    try:
      slicer.util.getNode(name).SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans))
    except:
      transnode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', name)
      transnode.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans))

  #--------------------初始化-----------------------------------------------------------------------
  def onApply(self):
    #在此处链接脚踏板开关
    # self._received_thread_ = threading.Thread(target=self.dealigt, args=(self,))
    # # print("thread")
    # self._is_running_ = True
    # # print("thread1")
    # self._received_thread_.setDaemon(True)
    # # print("thread2")
    # self._received_thread_.setName("Seria124")
    # self._received_thread_.start()
    if self.ui.CTMRI.checked:
      slicer.modules.withimage.widgetRepresentation().self().StartPedal()
      layout = qt.QHBoxLayout(self.ui.widget_4)
      layout.addWidget(slicer.modules.withimage.widgetRepresentation())
      layout.setContentsMargins(0,0,0,0)
      slicer.modules.withimage.widgetRepresentation().self().ui.ConfirmPoint.clicked.connect(self.MainChangePage)
    else:
      self.StartPedal()
    # if self.ui.CTMRI.checked:
    #   slicer.util.findChild(slicer.util.mainWindow(),"TopWidget").show()
    #   slicer.util.findChild(slicer.util.mainWindow(),"MainToolBar").show()
    #   slicer.util.findChild(slicer.util.mainWindow(),"NoImageWidget").hide()
    #   slicer.util.findChild(slicer.util.mainWindow(),"ModulePanel").setMaximumWidth(99999)
    #   slicer.util.moduleSelector().selectModule("Case_main")
    #   slicer.util.findChild(slicer.util.mainWindow(),"NoImage").hide()

    # elif self.ui.Deformation.checked:
    #   print('开始监听信号')
    #   self.ui.ForwardToolButton.setEnabled(True)
    #   self.onPrepare()
    #   self.ifsend03=1
    #   message = qt.QMessageBox(qt.QMessageBox.Information,'提示',"初始化成功！",qt.QMessageBox.Ok)
    #   message.button(qt.QMessageBox().Ok).setText('确定')
    #   message.exec()
    #   self.ui.tool1.setEnabled(True)

    #   try:
    #     self.onstartDJ()
    #     print('###########蓝牙串口已开启###########')
    #   except:
    #     pass
      # s1 = 0
      # s2 = 1
      # s3 = 1
      # s4 = 2
      # s5 = 0
      # s6 = 0
      # s7 = 0
      # s8 = f'{int(self.ui.tool2.enabled)}' + f'{int(self.ui.tool3.enabled)}' + f'{int(self.ui.tool4.enabled)}' + f'{int(self.ui.tool5.enabled)}' + f'{int(self.ui.tool6.enabled)}'+'@\n'
      # self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
      # print('已发送',f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())

      # NoImageToolWidget = slicer.util.findChild(slicer.util.mainWindow(),"NoImageToolWidget")
      # NoImageToolWidget.setVisible(True)
      # self.ui.ToolWidget.show()
      # self.ui.TitleWidget.show()
      # self.ui.ForwardToolButton.click()


  #加载数据-----------------------------
  def onPrepare(self):
    slicer.util.loadScene(self.FilePath+'/cj/cj.mrml')
    # slicer.util.loadScene("D:/data/cj1/cj1.mrml")
    Node1 = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLIGTLConnectorNode')
    Node1.Start()
    w = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLFiducialRegistrationWizardNode")
    w = slicer.util.getNode('FiducialRegistrationWizard')
    w.SetRegistrationModeToRigid()
    w.SetUpdateModeToManual()
    FemurToTool1node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'FromToTo_femur')
    tibiaToTool2node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'FromToTo_tibia')
    w.SetOutputTransformNodeId(FemurToTool1node.GetID())
    From1node = slicer.util.getNode('From')
    w.SetAndObserveFromFiducialListNodeId(From1node.GetID())
    To1node = slicer.util.getNode('To')
    w.SetAndObserveToFiducialListNodeId(To1node.GetID())
    probeToTransformNode = slicer.util.getNode("StylusTipToStylus")
    w.SetProbeTransformFromNodeId(probeToTransformNode.GetID())

    StylusNode = slicer.util.getNode('StylusToTracker')
    KnifeNode = slicer.util.getNode('KnifeToTracker')
    FemurNode = slicer.util.getNode('DianjiToTracker1')
    TibiaNode = slicer.util.getNode('TibiaToTracker')
    self.transform1 = np.array([[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]])
    self.transform2 = self.transform1
    self.transform3 = self.transform1
    self.transform4 = self.transform1
    self.count = 0
    self.count1 = 0
    # 所有观察者调用同一个函数
    # StylusNode.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.StateChange)
    # KnifeNode.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.StateChange)
    # FemurNode.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.StateChange)
    # TibiaNode.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.StateChange)

  # #针刀槽股骨胫骨状态图标(在setup中调用)
  # def onState(self):

  #   #为按钮设置图标
  #   self.ui.tool1.setIcon(qt.QIcon(self.iconsPath+'/TwoEye.png'))
  #   self.ui.tool1.setToolTip('光学指示灯')
  #   self.ui.tool7.setIcon(qt.QIcon(self.iconsPath+'/navigation.png'))
  #   self.ui.tool7.setToolTip('机械臂指示灯')
  #   self.ui.tool2.setIcon(qt.QIcon(self.iconsPath+'/needle.png'))
  #   self.ui.tool2.setToolTip('针指示灯')
  #   self.ui.tool3.setIcon(qt.QIcon(self.iconsPath+'/knife.png'))
  #   self.ui.tool3.setToolTip('刀槽指示灯')
  #   self.ui.tool4.setIcon(qt.QIcon(self.iconsPath+'/femur.png'))
  #   self.ui.tool4.setToolTip('股骨指示灯')
  #   self.ui.tool5.setIcon(qt.QIcon(self.iconsPath+'/tibia.png'))
  #   self.ui.tool5.setToolTip('胫骨指示灯')   
  #   self.ui.tool6.setIcon(qt.QIcon(self.iconsPath+'/Plane.png'))
  #   self.ui.tool6.setToolTip('截骨面指示灯')  
   
  #   self.ui.tool1.setEnabled(False)
  #   self.ui.tool2.setEnabled(False)
  #   self.ui.tool3.setEnabled(False)
  #   self.ui.tool4.setEnabled(False)
  #   self.ui.tool5.setEnabled(False)
  #   self.ui.tool6.setEnabled(False)
  #   self.ui.tool7.setEnabled(False)

  def StateChange(self,transformNode,unusedArg2=None, unusedArg3=None):
    self.count += 1
    if self.count%50==0:
      self.count1 += 1
      self.count=1
      StylusNode=slicer.util.getNode('StylusToTracker')
      KnifeNode = slicer.util.getNode('KnifeToTracker')
      FemurNode = slicer.util.getNode('DianjiToTracker1')
      TibiaNode = slicer.util.getNode('TibiaToTracker')
      transform1 = slicer.util.arrayFromTransformMatrix(StylusNode)
      transform2 = slicer.util.arrayFromTransformMatrix(KnifeNode)
      transform3 = slicer.util.arrayFromTransformMatrix(FemurNode)
      transform4 = slicer.util.arrayFromTransformMatrix(TibiaNode)
      if (transform1 == self.transform1).all():
        self.ui.tool2.setEnabled(False)        
      else:
        self.ui.tool2.setEnabled(True)
        self.transform1 = transform1

      if (transform2 == self.transform2).all():
        self.ui.tool3.setEnabled(False)        
      else:  
        self.ui.tool3.setEnabled(True)
        self.transform2 = transform2
      if (transform3 == self.transform3).all():
        self.ui.tool4.setEnabled(False)
      else:
        self.ui.tool4.setEnabled(True)
        self.transform3 = transform3

      if (transform4 == self.transform4).all():
        self.ui.tool5.setEnabled(False)
      else:       
        self.ui.tool5.setEnabled(True)
        self.transform4 = transform4
      #向小屏幕发送外翻角屈膝角以及工具状态
      s1 = 1
      s2 = 0
      try:
        s3 = round(self.currentY,2)  # 外翻
        s4 = round(self.currentX,2)   # 屈膝
      except:
        s3 = 0  # 外翻
        s4 = 0  # 屈膝

      s5 = 0
      s6 = 0
      s7 = 0
      s8 = f'{int(self.ui.tool2.enabled)}' + f'{int(self.ui.tool3.enabled)}' + f'{int(self.ui.tool4.enabled)}' + f'{int(self.ui.tool5.enabled)}' + f'{int(self.ui.tool6.enabled)}'+'@\n'
      self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
      #print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')

 
  def OperationTechnology(self):
    try:
      self.Image1.findChild("QLabel").delete()
    except:
      pass
    PngLabel = qt.QLabel(self.Image1)
    PngLabel.resize(self.Image1.width,self.Image1.height)
    PngLabel.setScaledContents(True)
    PngLabel.setStyleSheet("QLabel{background-color:transparent;}")
    if self.ui.CTMRI.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/CTMRI.png') 
    elif self.ui.Deformation.checked: 
      pixmap = qt.QPixmap(self.iconsPath+'/GuBianXing.png') 
    
    pixmap = pixmap.scaled(1024,1024,qt.Qt.KeepAspectRatio,qt.Qt.SmoothTransformation)
    PngLabel.setPixmap(pixmap)  
    PngLabel.resize(719,449) 
    PngLabel.show()

  def OperationTool(self):
    try:
      self.Image2.findChild("QLabel").delete()
    except:
      pass
    PngLabel = qt.QLabel(self.Image2)
    PngLabel.resize(self.Image2.width,self.Image2.height)
    PngLabel.setScaledContents(True)
    PngLabel.setStyleSheet("QLabel{background-color:transparent;}")
    if self.ui.FourAndOne.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/FourAndOne.png')  
    elif self.ui.PSI.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/PSI.png')  
    elif self.ui.ZhiWei.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/ZhiWei.png')  
    elif self.ui.ZhiXiang.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/ZhiXiang.png')  

    pixmap = pixmap.scaled(1024,1024,qt.Qt.KeepAspectRatio,qt.Qt.SmoothTransformation)
    PngLabel.setPixmap(pixmap)  
    PngLabel.resize(719,449) 
    PngLabel.show()

  def OperationOrder(self):
    try:
      self.Image3.findChild("QLabel").delete()
    except:
      pass
    PngLabel = qt.QLabel(self.Image3)
    PngLabel.resize(self.Image3.width,self.Image3.height)
    PngLabel.setScaledContents(True)
    PngLabel.setStyleSheet("QLabel{background-color:transparent;}")
    pixmap = qt.QPixmap(self.iconsPath+'/PSI.png')   
    if self.ui.TibiaFirst.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/TibiaFirst.png') 
    elif self.ui.FemurFirst.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/FemurFirst.png')
    PngLabel.setPixmap(pixmap)   
    PngLabel.resize(719,449)
    PngLabel.show()

  #间隙平衡选择
  def OperationClearance(self):    
    try:
      self.Image4.findChild("QLabel").delete()
    except:
      pass
    PngLabel = qt.QLabel(self.Image4)
    PngLabel.resize(self.Image4.width,self.Image4.height)
    PngLabel.setScaledContents(True)
    PngLabel.setStyleSheet("QLabel{background-color:transparent;}")
    if self.ui.JieGu.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/JieGu.png')   
    elif self.ui.RuanZuZhi.checked:
      pixmap = qt.QPixmap(self.iconsPath+'/RuanZuZhi.png')   
    
    PngLabel.setPixmap(pixmap)  
    PngLabel.resize(719,449) 
    PngLabel.show()

  # #四张图片是否显示
  # def FourImage(self,bool):    
  #   self.Image1 = slicer.util.findChild(slicer.util.mainWindow(),"Image1")
  #   self.Image2 = slicer.util.findChild(slicer.util.mainWindow(),"Image2")
  #   self.Image3 = slicer.util.findChild(slicer.util.mainWindow(),"Image3")
  #   self.Image4 = slicer.util.findChild(slicer.util.mainWindow(),"Image4")
  #   self.Image1.setVisible(bool)
  #   self.Image2.setVisible(bool)
  #   self.Image3.setVisible(bool)
  #   self.Image4.setVisible(bool)

  #------------------------------系统准备--------------------------------
  # def HideAllSystemWidget(self,widget):
  #   self.ui.powerOnWidget.setVisible(False)
  #   self.ui.positionWidget.setVisible(False)
  #   self.ui.signInWidget.setVisible(False)
  #   self.ui.femurSystemWidget.setVisible(False)
  #   self.ui.tibiaSystemWidget.setVisible(False)
  #   self.ui.testWidget.setVisible(False)
  #   widget.setVisible(True)
  
  # def onSystemButton(self,button):
  #   #手术室准备->系统准备->工具->股骨->胫骨->检测
  #   self.ui.powerOnButton.setChecked(False)
  #   self.ui.positionButton.setChecked(False)
  #   self.ui.femurSystemButton.setChecked(False)
  #   self.ui.tibiaSystemButton.setChecked(False)
  #   self.ui.testButton.setChecked(False)
  #   self.ui.signInButton.setChecked(False)
  #   self.ui.SystemTool.setVisible(False)
  #   button.setChecked(True)
  #   if button == self.ui.powerOnButton:
  #     # self.HideAllSystemWidget(self.ui.powerOnWidget)
  #     self.setSystemCheckBoxState(self.ui.powerOn1)
  #     self.ui.SystemTool.setVisible(True)
  #     self.ui.SystemConfirm.setEnabled(True)
  #     self.powerOnNum = 0
  #   elif button == self.ui.positionButton:
  #     # self.HideAllSystemWidget(self.ui.positionWidget)
  #   elif button == self.ui.signInButton:
  #     # self.HideAllSystemWidget(self.ui.signInWidget)
  #     self.ui.SystemTool.setVisible(True)
  #     self.ui.SystemConfirm.setEnabled(True)
  #     self.setSystemCheckBoxState(self.ui.test1)
  #     self.testNum = 0

  #   elif button == self.ui.femurSystemButton:
  #     # self.HideAllSystemWidget(self.ui.femurSystemWidget)
  #   elif button == self.ui.tibiaSystemButton:
  #     # self.HideAllSystemWidget(self.ui.tibiaSystemWidget)
  #   elif button == self.ui.testButton:
  #     # self.HideAllSystemWidget(self.ui.testWidget)

  # def onSystemConfirm(self):
  #   PowerOnCheckBox = [self.ui.powerOn1,self.ui.powerOn2,self.ui.powerOn3]
  #   TestCheckBox = [self.ui.test1,self.ui.test2,self.ui.test3,self.ui.test4,self.ui.test5]
  #   if self.ui.powerOnButton.checked:
  #     PowerOnCheckBox[self.powerOnNum].setChecked(True)
  #     if self.powerOnNum == 2:
  #       self.ui.powerOn3.setStyleSheet("None")
  #       self.ui.SystemConfirm.setEnabled(False)
  #     else:
  #       self.setSystemCheckBoxState(PowerOnCheckBox[self.powerOnNum+1])
  #       self.powerOnNum += 1
  #   elif self.ui.signInButton.checked:
  #     TestCheckBox[self.testNum].setChecked(True)
  #     if self.testNum == 4:
  #       self.ui.SystemConfirm.setEnabled(False)
  #       self.ui.test5.setStyleSheet("None")
  #     else:
  #       self.setSystemCheckBoxState(TestCheckBox[self.testNum+1])
  #       self.testNum += 1

  # def onSystemReset(self):
  #   PowerOnCheckBox = [self.ui.powerOn1,self.ui.powerOn2,self.ui.powerOn3]
  #   TestCheckBox = [self.ui.test1,self.ui.test2,self.ui.test3,self.ui.test4,self.ui.test5]
  #   if self.ui.powerOnButton.checked:
  #     for i in range(0,len(PowerOnCheckBox)):
  #       PowerOnCheckBox[i].setChecked(False)

  #     self.setSystemCheckBoxState(self.ui.powerOn1)
  #     self.ui.SystemConfirm.setEnabled(True)
  #     self.powerOnNum = 0
  #   elif self.ui.signInButton.checked:
  #     for i in range(0,len(TestCheckBox)):
  #       TestCheckBox[i].setChecked(False)
  #     self.ui.SystemConfirm.setEnabled(True)
  #     self.setSystemCheckBoxState(self.ui.test1)
  #     self.testNum = 0
  # #为系统准备按钮添加Mask  
  # def buttonMask(self,name,button):    
  #   abc=qt.QPixmap(os.path.join(self.iconsPath,name+".png"))
  #   button.setMask(abc.mask())
  #   icon1A = qt.QIcon()
  #   icons1APath = os.path.join(self.iconsPath, name+".png")
  #   icon1A.addPixmap(qt.QPixmap(icons1APath))
  #   button.setIcon(icon1A)
  #   button.setFlat(True)
  #   print(os.path.join(self.iconsPath,name+".png"))
  
  # def setSystemCheckBoxState(self,checkBox):
  #   for i in range (0,len(self.ui.SystemWidget.findChildren("QCheckBox"))):
  #     self.ui.SystemWidget.findChildren("QCheckBox")[i].setStyleSheet("None")
  #   checkBox.setStyleSheet("background:#515151;color:#7bcd27;font-weight:bold;")

  def setCheckBoxState(self,checkBox,Label):
    for i in range (0,len(self.ui.femurPointWidget.findChildren("QCheckBox"))):
      self.ui.femurPointWidget.findChildren("QCheckBox")[i].setStyleSheet("None")
    for i in range (0,len(self.ui.tibiaPointWidget.findChildren("QCheckBox"))):
      self.ui.tibiaPointWidget.findChildren("QCheckBox")[i].setStyleSheet("None")

    for i in range (0,len(self.ui.femurPointWidget.findChildren("QLabel"))):
      self.ui.femurPointWidget.findChildren("QLabel")[i].setStyleSheet("None")
    for i in range (0,len(self.ui.tibiaPointWidget.findChildren("QCheckBox"))):
      self.ui.tibiaPointWidget.findChildren("QLabel")[i].setStyleSheet("None")

    checkBox.setStyleSheet("background:#515151;color:#7bcd27;font-weight:bold;")   
    Label.setStyleSheet("background:#515151;color:#7bcd27;font-weight:bold;")   

#-----------------ssm模型（股骨配准 And 胫骨配准）--------------------

  def EnterSet(self):
    self.ui.SelectWidget.setVisible(False)
    self.ui.NextArea.setVisible(False)
    self.ui.StopSelect.setVisible(False)
    self.ui.Confirm1.setEnabled(False)
    self.ui.PointReset.setEnabled(False)
    self.ui.SingleSelect.setChecked(True)
    self.ui.femurWidget2.setVisible(False)

  #点击前进到股骨配准和胫骨配准时调用
  def FemurOrTibia(self):
    From1node = slicer.util.getNode('From')
    From1node.RemoveAllControlPoints()
    Tonode = slicer.util.getNode('To')
    Tonode.RemoveAllControlPoints()
    if self.ui.centerWidget.currentIndex == 3:
      points = np.array([[2.421287, -1.137471, -31.445272],
                         [16.180315, -33.439308, -14.108915],
                         [-27.91506, -26.189674, -17.669632],
                         [23.150414, -9.324886, -35.455048],
                         [-21.972315, -4.575426, -38.243401],
                         [36.633526, -13.987321, -14.000193],
                         [-37.562634, -1.810003, -15.941791],
                         [23.380989, 24.045118, -1.354824],
                         [5.172663, 17.771029, -28.148647]])
      Transform_tmp=slicer.util.getNode('DianjiToTracker1')
      Tonode.SetAndObserveTransformNodeID(Transform_tmp.GetID())
    elif self.ui.centerWidget.currentIndex == 4 :
      points = np.array([[-0.13547, -2.620466, 37.901165],
                         [15.534579, 21.889713, -5.486698],
                         [19.430536, -5.408284, 30.107407],
                         [-17.972166, 1.875922, 31.642845]])
      Transform_tmp=slicer.util.getNode('TibiaToTracker')
      Tonode.SetAndObserveTransformNodeID(Transform_tmp.GetID())
    # if slicer.modules.NoImageWelcomeWidget.judge == 'L':#左腿
    #   for i in range(len(points)):
    #     points[i][0]=-points[i][0]
    for i in range(len(points)):
      From1node.AddControlPoint(points[i][0], points[i][1], points[i][2])

  #视图显示 0显示图片视图 1图片视图+三维视图 2三维视图
  def ThreeDViewAndImageWidget(self,index):        
    if index == 0:#显示图片视图
      self.FourWidget.setVisible(False)
      self.noimageWidget.setVisible(True)
    elif index == 1:#两者都显示
      self.FourWidget.setVisible(True)
      self.noimageWidget.setVisible(True)
    elif index == 2:#显示三维窗口
      self.FourWidget.setVisible(True)
      self.noimageWidget.setVisible(False)

  #切换三维视图和图片视图
  def onSwitch(self):
    #图片widget
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
    self.ThreeDViewAndImageWidget(self.SwitchState)
    if self.SwitchState == 0:
      self.pixmap = qt.QPixmap(self.iconsPath+'/'+self.pngName+'.png')
      self.PngLabel.setPixmap(self.pixmap)
      self.PngLabel.resize(self.noimageWidget.width,self.noimageWidget.height)
      self.SwitchState = 1
    elif self.SwitchState == 1:
      self.pixmap = qt.QPixmap(self.iconsPath+'/'+self.pngName+'_1.png')
      self.PngLabel.setPixmap(self.pixmap)
      self.PngLabel.resize(self.noimageWidget.width,self.noimageWidget.height)
      self.SwitchState = 2
    elif self.SwitchState == 2:            
      self.SwitchState = 0

  #股骨校准时调用该函数显示图片
  def onFemurRadioButton(self):
    for i in range(0,len(self.noimageWidget.findChildren("QLabel"))):
      self.noimageWidget.findChildren("QLabel")[-1].clear()
    self.PngLabel = qt.QLabel(self.noimageWidget)
    self.PngLabel.resize(self.noimageWidget.width,self.noimageWidget.height)
    self.PngLabel.setScaledContents(True)
    self.PngLabel.setStyleSheet("QLabel{background-color:transparent;}")
    if self.noimageWidget.width>1000:
        self.pixmap = qt.QPixmap(self.iconsPath+'/femur1.png')
    else:
        self.pixmap = qt.QPixmap(self.iconsPath+'/femur1_1.png')
    self.img_label_setimage(self.pixmap)#新UI
      
    #self.pixmap = self.pixmap.scaled(1437,897,qt.Qt.KeepAspectRatio,qt.Qt.SmoothTransformation)
    self.PngLabel.setPixmap(self.pixmap)   
    self.PngLabel.show()
    self.pngName = "femur1"
    #self.ui.femurPoint1.setChecked(True)
    self.setCheckBoxState(self.ui.femurPoint1,self.ui.femurPoint1Label)
    self.FemurPng = 2
    self.ui.Select1.setEnabled(True)
  #胫骨校准时调用该函数选择图片
  def onTibiaRadioButton(self):
    for i in range(0,len(self.noimageWidget.findChildren("QLabel"))):
      self.noimageWidget.findChildren("QLabel")[-1].clear()
    self.PngLabel = qt.QLabel(self.noimageWidget)
    self.PngLabel.setScaledContents(True)
    self.PngLabel.setStyleSheet("QLabel{background-color:transparent;}")
    if self.noimageWidget.width>1000:
      self.pixmap = qt.QPixmap(self.iconsPath+'/tibia1.png')
    else:
      self.pixmap = qt.QPixmap(self.iconsPath+'/tibia1_1.png')
    self.img_label_setimage(self.pixmap)#新UI
    self.PngLabel.setPixmap(self.pixmap)
    self.PngLabel.resize(self.noimageWidget.width,self.noimageWidget.height)
    self.PngLabel.show()
    self.setCheckBoxState(self.ui.tibiaPoint1,self.ui.tibiaPoint1Label)
    self.TibiaPng = 2
    self.ui.Select1.setEnabled(True)

  # 选择一个点
  def SelectSinglePoint(self):
    Number = ["⑳", "⑲", "⑱", "⑰", "⑯", "⑮", "⑭", "⑬", "⑫", "⑪", "⑩", "⑨", "⑧", "⑦", "⑥", "⑤", "④", "③", "②", "①"]
    probeToTransformNode = slicer.util.getNode("StylusTipToStylus")
    toMarkupsNode = slicer.util.getNode("To")
    if self.VRstate:
      toMarkupsNode.AddControlPoint(self.vrPoint)
    else:
      slicer.modules.fiducialregistrationwizard.logic().AddFiducial(probeToTransformNode, toMarkupsNode)
    if self.ui.centerWidget.currentIndex == 3:
      self.PointMove('To', 'DianjiToTracker1')
      try:
        if self.FemurPng > 12:
          if self.JudgePointInRightPosition(toMarkupsNode, 'Femur'):
            label_femur = [self.ui.femurPoint10Label, self.ui.femurPoint11Label, self.ui.femurPoint12Label,
                           self.ui.femurPoint13Label, self.ui.femurPoint14Label]
            label_femur[self.FemurPng - 13].setText(Number[19 - self.FemurPointCount[self.FemurPng - 13]])
            self.FemurPointCount[self.FemurPng - 13] += 1
          else:#移除不在区域内的点
            num = toMarkupsNode.GetNumberOfControlPoints()
            toMarkupsNode.RemoveNthControlPoint(num - 1)
      except:
        print(1)
    else:
      self.PointMove('To', 'TibiaToTracker')
      try:
        if self.FemurPng > 7:
          if self.JudgePointInRightPosition(toMarkupsNode, 'Tibia'):
            label_femur = [self.ui.tibiaPoint7Label, self.ui.tibiaPoint8Label, self.ui.tibiaPoint9Label]
            label_femur[self.TibiaPng - 8].setText(Number[19 - self.TibiaPointCount[self.TibiaPng - 8]])
            self.TibiaPointCount[self.TibiaPng - 8] += 1
          else:#移除不在区域内的点
            num = toMarkupsNode.GetNumberOfControlPoints()
            toMarkupsNode.RemoveNthControlPoint(num - 1)
      except:
        print(1)

  def JudgePointInRightPosition(self, PointNode, FOrT):
    point1 = [0, 0, 0]
    num = PointNode.GetNumberOfControlPoints()
    PointNode.GetNthControlPointPositionWorld(num - 1, point1)
    if FOrT == 'Femur':
      mark = ['内侧远端', '外侧远端', '内侧后髁', '外侧后髁', '外侧皮质高点']
      point2 = [0, 0, 0]
      print(mark[self.FemurPng - 13])
      slicer.util.getNode(mark[self.FemurPng - 13]).GetNthControlPointPositionWorld(0, point2)
    else:
      mark = ['内侧高点', '外侧高点', '胫骨结节']
      point2 = [0, 0, 0]
      slicer.util.getNode(mark[self.TibiaPng - 8]).GetNthControlPointPositionWorld(0, point2)
    d = self.distance(np.array(point1), np.array(point2))
    if d < 20:
      return 1
    else:
      return 0

  # 开始选择
  def MoreStart(self):
    Stylus = slicer.util.getNode("StylusTipToStylus")
    self.FemurObserver = Stylus.AddObserver(
      slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onAddMarkups)

  def onAddMarkups(self, unusedArg1=None, unusedArg2=None, unusedArg3=None):
    Number = ["⑳", "⑲", "⑱", "⑰", "⑯", "⑮", "⑭", "⑬", "⑫", "⑪", "⑩", "⑨", "⑧", "⑦", "⑥", "⑤", "④", "③", "②", "①"]
    probeToTransformNode = slicer.util.getNode("StylusTipToStylus")
    toMarkupsNode = slicer.util.getNode("To")
    if self.VRstate:
      toMarkupsNode.AddControlPoint(self.vrPoint)
    else:
      slicer.modules.fiducialregistrationwizard.logic().AddFiducial(probeToTransformNode, toMarkupsNode)
    if self.ui.centerWidget.currentIndex == 3:
      self.PointMove('To', 'DianjiToTracker1')
      if self.FemurPng > 10:
        if self.JudgePointInRightPosition(toMarkupsNode, 'Femur'):
          label_femur = [self.ui.femurPoint10Label, self.ui.femurPoint11Label, self.ui.femurPoint12Label,
                         self.ui.femurPoint13Label, self.ui.femurPoint14Label]
          label_femur[self.FemurPng - 11].setText(Number[19 - self.FemurPointCount[self.FemurPng - 11]])
          self.FemurPointCount[self.FemurPng - 11] += 1
    else:
      self.PointMove('To', 'TibiaToTracker')
      if self.FemurPng > 7:
        if self.JudgePointInRightPosition(toMarkupsNode, 'Tibia'):
          label_femur = [self.ui.tibiaPoint7Label, self.ui.tibiaPoint8Label, self.ui.tibiaPoint9Label]
          label_femur[self.TibiaPng - 8].setText(Number[19 - self.TibiaPointCount[self.TibiaPng - 8]])
          self.TibiaPointCount[self.TibiaPng - 8] += 1
  #停止选择
  def onStopSelect(self):
    Stylus = slicer.util.getNode("StylusTipToStylus")
    Stylus.RemoveObserver(self.FemurObserver)
    self.ui.Select1.setVisible(True)
    self.ui.StopSelect.setVisible(False)
  
  def SwitchFemur(self):
    femurPointCheckBox = [self.ui.femurPoint1,self.ui.femurPoint2,self.ui.femurPoint3,self.ui.femurPoint4,self.ui.femurPoint5,
                          self.ui.femurPoint6,self.ui.femurPoint7,self.ui.femurPoint8,self.ui.femurPoint9,self.ui.femurPoint15,self.ui.femurPoint16,self.ui.femurPoint10,
                          self.ui.femurPoint11,self.ui.femurPoint12,self.ui.femurPoint13,self.ui.femurPoint14]
    femurPointLabel = [self.ui.femurPoint1Label,self.ui.femurPoint2Label,self.ui.femurPoint3Label,self.ui.femurPoint4Label,self.ui.femurPoint5Label,
                      self.ui.femurPoint6Label,self.ui.femurPoint7Label,self.ui.femurPoint8Label,self.ui.femurPoint9Label,self.ui.femurPoint15Label,self.ui.femurPoint16Label,self.ui.femurPoint10Label,
                      self.ui.femurPoint11Label,self.ui.femurPoint12Label,self.ui.femurPoint13Label,self.ui.femurPoint14Label]
    if self.noimageWidget.width>1000:
        self.pixmap = qt.QPixmap(self.iconsPath+'/femur'+str(self.FemurPng)+'.png')
    else:
      self.pixmap = qt.QPixmap(self.iconsPath+'/femur'+str(self.FemurPng)+'_1.png')
    self.PngLabel.setPixmap(self.pixmap)
    self.PngLabel.resize(self.noimageWidget.width,self.noimageWidget.height)
    self.PngLabel.show()
    self.img_label_setimage(self.pixmap)#新UI
    femurPointCheckBox[self.FemurPng-2].setChecked(True)
    if self.FemurPng-1 == 16:      
      self.ui.femurPoint14.setStyleSheet("None")
      self.ui.femurPoint14Label.setStyleSheet("None")
      self.ui.NextArea.setEnabled(False)
      self.ui.Confirm1.setEnabled(True)
      
    else:
      if self.FemurPng-1<9:
        self.setCheckBoxState(femurPointCheckBox[self.FemurPng-1],femurPointLabel[self.FemurPng-1])
        self.pngName = "femur"+str(self.FemurPng)
      else:
        self.setCheckBoxState(femurPointCheckBox[self.FemurPng-1],femurPointLabel[self.FemurPng-1])
        self.pngName = "femur"+str(self.FemurPng-2)
    self.FemurPng += 1
    
  def SwitchTibia(self):
    tibiaPointCheckBox = [self.ui.tibiaPoint1,self.ui.tibiaPoint2,self.ui.tibiaPoint3,self.ui.tibiaPoint4,self.ui.tibiaPoint5,
                          self.ui.tibiaPoint6,self.ui.tibiaPoint7,self.ui.tibiaPoint8,self.ui.tibiaPoint9]
    tibiaPointLabel = [self.ui.tibiaPoint1Label,self.ui.tibiaPoint2Label,self.ui.tibiaPoint3Label,self.ui.tibiaPoint4Label,self.ui.tibiaPoint5Label,
                      self.ui.tibiaPoint6Label,self.ui.tibiaPoint7Label,self.ui.tibiaPoint8Label,self.ui.tibiaPoint9Label]
    if self.noimageWidget.width>1000:
      self.pixmap = qt.QPixmap(self.iconsPath+'/tibia'+str(self.TibiaPng)+'.png')
    else:
      self.pixmap = qt.QPixmap(self.iconsPath+'/tibia'+str(self.TibiaPng)+'_1.png')
    self.PngLabel.setPixmap(self.pixmap)
    self.PngLabel.resize(self.noimageWidget.width,self.noimageWidget.height)
    self.PngLabel.show()
    self.img_label_setimage(self.pixmap)#新UI
    tibiaPointCheckBox[self.TibiaPng-2].setChecked(True)
    if self.TibiaPng-1 == 9:
      self.ui.NextArea.setEnabled(False)
      self.ui.tibiaPoint9.setStyleSheet("None")
      self.ui.tibiaPoint9Label.setStyleSheet("None")
      self.ui.Confirm1.setEnabled(True)
    else:
      self.setCheckBoxState(tibiaPointCheckBox[self.TibiaPng-1],tibiaPointLabel[self.TibiaPng-1])
      self.pngName = "Tibia"+str(self.TibiaPng)
    self.TibiaPng += 1

  # def peizhunBtnstatus(self,btn,label,status):
  #   if status == 0:
  #     btn.setChecked(False)
  #     label.setStyleSheet("color:#c8c8c8;")
  #   if status == 1:
  #     btn.setChecked(True)
  #     label.setStyleSheet("color:#7cbd27;")
  #   if status == 2:
  #     btn.setStyleSheet("background:#faa21c;color:#faa21c")
  #     label.setStyleSheet("color:#faa21c;")

  #整体切换图片函数、单选点、多选点函数
  def onSelect1(self,whoSend=None):
    # rrr = self.ui.centerWidget.currentIndex
    # if rrr == 3:
    #   btns = self.ui.checkpoints_widget.findChildren('QPushButton')
    # if rrr == 4:
    #   btns = self.ui.checkpoints_widget_2.findChildren('QPushButton')
    # for btn in btns:
    #   if not btn.isChecked():
    #     if rrr == 3:
    #       self.peizhunBtnstatus(btn,'femurLabel'+btn.objectName[-1],2)
    #     if rrr == 4:
    #       self.peizhunBtnstatus(btn,'tibiaLabel'+btn.objectName[-1],2)


    self.ui.PointReset.setEnabled(True)
    print(self.FemurPng - 1)
    if self.ui.centerWidget.currentIndex == 3:
    # if self.ui.centerWidget.currentIndex == 3 :
      if self.FemurPng - 1 <10:
        self.SwitchFemur()
        self.SelectSinglePoint()
        if whoSend!='xiaopingmu':
          self.sendDian()
      elif self.FemurPng - 1 == 10:
        #选取H点
        self.onHPoint()
        self.SwitchFemur()
        self.ui.NextArea.setVisible(True)
        #self.Pedal1.SelectCurrentStatue(1)#切换状态
        self.ui.SelectWidget.setVisible(True)
        self.FemurPointCount=[0,0,0,0,0]

        if whoSend!='xiaopingmu':
          self.sendDian()
        self.onConfirm1_femur()
      
      elif self.FemurPng - 1 == 11:
        #股骨头球心的点
        self.onGuGuTou()

      else:
        if self.ui.SingleSelect.checked:
          self.SelectSinglePoint()
        else:
          self.MoreStart()
          self.ui.Select1.setVisible(False)
          self.ui.StopSelect.setVisible(True)

    elif self.ui.centerWidget.currentIndex == 4:
    # elif self.ui.centerWidget.currentIndex == 4 :
      self.ui.NextArea.setEnabled(True)
      if self.TibiaPng-1 < 6:
        self.SwitchTibia()
        self.SelectSinglePoint()
        if whoSend!='xiaopingmu':
          self.sendDian()
      elif self.TibiaPng-1 == 6:
        
        self.SwitchTibia()
        self.ui.NextArea.setVisible(True)
        #self.Pedal1.SelectCurrentStatue(3)#切换状态
        self.ui.SelectWidget.setVisible(True)
        self.TibiaPointCount = [0, 0, 0]
        if self.ui.SingleSelect.checked:
          self.SelectSinglePoint()
        else:
          self.MoreStart()
          self.ui.Select1.setVisible(False)
          self.ui.StopSelect.setVisible(True)
        if whoSend!='xiaopingmu':
          self.sendDian()
        self.onConfirm1_tibia()
      else:
        if self.ui.SingleSelect.checked:
          self.SelectSinglePoint()
        else:
          self.MoreStart()
          self.ui.Select1.setVisible(False)
          self.ui.StopSelect.setVisible(True)


#向小屏幕发送选取点位的信息
  def sendDian(self,reset=0):
    try:
      if reset==0:
        s1 = 0
        s2 = 2
        s3 = 0  # 股骨不重置
        s4 = 0  # 胫骨不重置
        if self.ui.centerWidget.currentIndex == 3:
          s5 = 0
        else:
          s5 = 1
          # 股骨或者胫骨图片
        if s5 == 0:
          s6 = self.FemurPng - 1  # 顺序
        else:
          s6 = self.TibiaPng - 1
        s7 = 0
        s8 = '0@\n'
        self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
        #print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
      else:
        s1 = 0
        s2 = 2
        if self.ui.centerWidget.currentIndex == 3:
          s3 = 1  # 股骨重置
          s4 = 0  # 胫骨不重置

        else:
          s3 = 0  # 股骨重置
          s4 = 1  # 胫骨不重置
        if self.ui.centerWidget.currentIndex == 3:
          s5 = 0
        else:
          s5 = 1
          # 股骨或者胫骨图片
        if s5 == 0:
          s6 = 1
        else:
          s6 = 1
        s7 = 0
        s8 = '0@\n'
        self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
        #print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
    except:
      pass

  def onNextArea(self,whoSend=None):
    if self.ui.centerWidget.currentIndex == 3 :
      self.SwitchFemur()
    elif self.ui.centerWidget.currentIndex == 4 :
      self.SwitchTibia()
    if whoSend!='xiaopingmu':
      self.sendDian()

  #选点重置函数
  def onPointReset(self):
    message = qt.QMessageBox(qt.QMessageBox.Information,'重置',"是否要重新选点？",qt.QMessageBox.Ok|qt.QMessageBox.Cancel)
    message.button(qt.QMessageBox().Ok).setText('是')
    message.button(qt.QMessageBox().Cancel).setText('否')
    c= message.exec()
    if c == qt.QMessageBox.Ok:
      self.ui.PointReset.setEnabled(False)
      femurPointCheckBox = [self.ui.femurPoint1,self.ui.femurPoint2,self.ui.femurPoint3,self.ui.femurPoint4,self.ui.femurPoint5,
                            self.ui.femurPoint6,self.ui.femurPoint7,self.ui.femurPoint8,self.ui.femurPoint9,self.ui.femurPoint10,
                            self.ui.femurPoint11,self.ui.femurPoint12,self.ui.femurPoint13,self.ui.femurPoint14]
      tibiaPointCheckBox = [self.ui.tibiaPoint1,self.ui.tibiaPoint2,self.ui.tibiaPoint3,self.ui.tibiaPoint4,self.ui.tibiaPoint5,
                            self.ui.tibiaPoint6,self.ui.tibiaPoint7,self.ui.tibiaPoint8,self.ui.tibiaPoint9]
      self.ui.Select1.setEnabled(True)
      self.ui.SingleSelect.setChecked(True)
      if self.ui.centerWidget.currentIndex == 3 :
        for i in range(0,len(femurPointCheckBox)):
          femurPointCheckBox[i].setChecked(False)      
        self.onFemurRadioButton()
      elif self.ui.centerWidget.currentIndex == 4:
        for i in range(0,len(tibiaPointCheckBox)):
          tibiaPointCheckBox[i].setChecked(False)
        self.onTibiaRadioButton()
      Tonode = slicer.util.getNode('To')
      Tonode.RemoveAllControlPoints()
      #发送点重置
      self.sendDian(1)
    elif c == qt.QMessageBox.Canel:
      pass


  #单选结束确认函数_gugu
  def onConfirm1_femur(self):
    ToNode=slicer.util.getNode("To")
    #将选择的点按名称加入场景中
    self.FemurPoints = ['开髓点','内侧凹点','外侧凸点','内侧远端','外侧远端','内侧后髁','外侧后髁','外侧皮质高点','A点']
    self.TibiaPoints = ['胫骨隆凸','胫骨结节','外侧高点','内侧高点']
    Points = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    if self.ui.centerWidget.currentIndex == 3 :
      Transform_tmp = slicer.util.getNode('DianjiToTracker1')
      for i in range(len(Points)):
        PointNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', self.FemurPoints[i])
        PointNode.AddControlPoint(Points[i])
        PointNode.SetDisplayVisibility(0)
        PointNode.SetAndObserveTransformNodeID(Transform_tmp.GetID())
    else:
      Transform_tmp = slicer.util.getNode('TibiaToTracker')
      for i in range(len(Points)):
        PointNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', self.TibiaPoints[i])
        PointNode.AddControlPoint(Points[i])
        PointNode.SetDisplayVisibility(0)
        PointNode.SetAndObserveTransformNodeID(Transform_tmp.GetID())
    femur_index=[0,6,5,4,3,2,1,7,8]
    ToNode.RemoveAllControlPoints()
    for i in range(len(Points)):
      ToNode.AddControlPoint(Points[femur_index[i]])
    p=slicer.util.arrayFromMarkupsControlPoints(ToNode)
    ToNode.RemoveAllControlPoints()
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      for i in range(len(p)):
        ToNode.AddControlPoint(-p[i][0],p[i][1],p[i][2])
    else:
      for i in range(len(p)):
        ToNode.AddControlPoint(p[i][0], p[i][1], p[i][2])
    Points = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    FromPoints = self.simple_femur()
    FromNode = slicer.util.getNode("From")
    FromNode.RemoveAllControlPoints()
    for i in range(len(FromPoints)):
      FromNode.AddControlPoint(FromPoints[i])
    w = slicer.util.getNode('FiducialRegistrationWizard')
    slicer.modules.fiducialregistrationwizard.logic().UpdateCalibration(w)
    transNode=slicer.util.getNode('FromToTo_femur')
    trans=slicer.util.arrayFromTransformMatrix(transNode)
    target1 = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    if self.ui.centerWidget.currentIndex == 3 :
      self.data=np.loadtxt(self.FilePath+'/femur.txt')
      # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      #   for i in range(len(self.data)):
      #     self.data[i][0] = -self.data[i][0]
      for i in range(0,len(self.data)):
        l=[-self.data[i][0],-self.data[i][1],self.data[i][2],1]
        self.data[i]=np.dot(trans,l)[0:3]
      index = [7841,6968,3089,8589,2161,7462, 2410,7457,7692]
    else:#胫骨
      self.data=np.loadtxt(self.FilePath+'/tibia.txt')
      # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      #   for i in range(len(self.data)):
      #     self.data[i][0] = -self.data[i][0]
      for i in range(0,len(self.data)):
        l=[-self.data[i][0],-self.data[i][1],self.data[i][2],1]
        self.data[i]=np.dot(trans,l)[0:3]
      index=[1910, 1291, 6676, 7247]

    for i in range(len(target1)):
      self.data = self.move(self.data, index[i], target1[i])
    data1=np.empty([len(self.data),3])
    for i in range(0,len(self.data)):
      data1[i]=np.array([-self.data[i][0],-self.data[i][1],self.data[i][2]])
    self.remesh(data1)
    if self.ui.centerWidget.currentIndex == 3 :
      self.model=slicer.util.loadModel(self.FilePath+'/Femur.vtk')
    else:
      self.model = slicer.util.loadModel(self.FilePath+'/Tibia.vtk')
    print("开始拟合")
    self.SsmNihe(transNode)
    print("拟合结束")
    #将模型置于股骨工具变化下
    # transNode1=slicer.util.getNode('FemurToReal')
    transformNode = slicer.util.getNode('DianjiToTracker1')
    # Ftrans3=slicer.util.arrayFromTransformMatrix(transformNode)
    # Ftrans3_ni=np.linalg.inv(Ftrans3)
    # transNode1.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans3_ni))
    #transNode.SetAndObserveTransformNodeID(transformNode.GetID())
    Tonode = slicer.util.getNode('To')
    Tonode.RemoveAllControlPoints()
    ToNode.SetAndObserveTransformNodeID(transformNode.GetID())

  #单选结束确认函数_jinggu
  def onConfirm1_tibia(self):

    ToNode = slicer.util.getNode("To")
    #将选择的点按名称加入场景中
    self.TibiaPoints =  ['胫骨隆凸','胫骨结节','外侧高点','内侧高点']
    Points = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    Transform_tmp = slicer.util.getNode('TibiaToTracker')
    point1 = [Points[0],Points[5],Points[4],Points[3]]
    tibia_index=[0,5,4,3,2,1]
    ToNode.RemoveAllControlPoints()
    for i in range(len(Points)):
      ToNode.AddControlPoint(Points[tibia_index[i]])
    
    Points = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    for i in range(len(self.TibiaPoints)):
      PointNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', self.TibiaPoints[i])
      PointNode.AddControlPoint(point1[i])
      PointNode.SetDisplayVisibility(0)
      PointNode.SetAndObserveTransformNodeID(Transform_tmp.GetID())
    #添加踝穴中心点
    PointNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '踝穴中心')
    PointNode.AddControlPoint((Points[4]+Points[5])/2)
    transformNode = slicer.util.getNode('TibiaToTracker')
    PointNode.SetAndObserveTransformNodeID(transformNode.GetID())
    PointNode.SetDisplayVisibility(0)
    p = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    ToNode.RemoveAllControlPoints()
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      for i in range(len(p)):
        ToNode.AddControlPoint(-p[i][0], p[i][1], p[i][2])
    else:
      for i in range(len(p)):
        ToNode.AddControlPoint(p[i][0], p[i][1], p[i][2])
    FromPoints = self.simple_tibia()
    FromNode = slicer.util.getNode("From")
    FromNode.RemoveAllControlPoints()
    for i in range(len(FromPoints)):
      FromNode.AddControlPoint(FromPoints[i])
    w = slicer.util.getNode('FiducialRegistrationWizard')
    transNode = slicer.util.getNode('FromToTo_tibia')
    w.SetOutputTransformNodeId(transNode.GetID())
    slicer.modules.fiducialregistrationwizard.logic().UpdateCalibration(w)



    for i in range(2):                    #移除不用于校准的点
      ToNode.RemoveNthControlPoint(4)
    slicer.modules.fiducialregistrationwizard.logic().UpdateCalibration(w)
    trans = slicer.util.arrayFromTransformMatrix(transNode)
    target1 = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    self.data=np.loadtxt(self.FilePath+'/tibia.txt')
    # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
    #   for i in range(len(self.data)):
    #     self.data[i][0] = -self.data[i][0]
    for i in range(0,len(self.data)):
      l=[-self.data[i][0],-self.data[i][1],self.data[i][2],1]
      self.data[i]=np.dot(trans,l)[0:3]
    index=[1910, 1291, 6676, 7247]
    for i in range(len(target1)):
      self.data = self.move(self.data, index[i], target1[i])
    data1=np.empty([len(self.data),3])
    for i in range(0,len(self.data)):
      data1[i]=np.array([-self.data[i][0],-self.data[i][1],self.data[i][2]])
    self.remesh(data1)
    self.model = slicer.util.loadModel(self.FilePath+'/Tibia.vtk')
    self.SsmNihe(transNode)
    #将模型置于jinggu工具变化下
    # transNode1=slicer.util.getNode('TibiaToReal')
    transformNode = slicer.util.getNode('TibiaToTracker')
    # Ftrans3=slicer.util.arrayFromTransformMatrix(transformNode)
    # Ftrans3_ni=np.linalg.inv(Ftrans3)
    # transNode1.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans3_ni))
    #transNode.SetAndObserveTransformNodeID(transformNode.GetID())
    Tonode = slicer.util.getNode('To')
    Tonode.RemoveAllControlPoints()
    ToNode.SetAndObserveTransformNodeID(transformNode.GetID())


  def SsmNihe(self,transNode):
    ToNode = slicer.util.getNode("To")
    transNode.Inverse()
    ToNode.SetAndObserveTransformNodeID(transNode.GetID())
    self.model.SetAndObserveTransformNodeID(transNode.GetID())
    self.model.HardenTransform()
    ToNode.HardenTransform()
    transNode.Inverse()

    if self.ui.centerWidget.currentIndex == 3 :
      # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      #   self.FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '左右镜像')
      #   FemurTrans=np.array([[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
      #   self.FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
      #   self.model.SetAndObserveTransformNodeID(self.FemurTransform.GetID())
      #   self.model.HardenTransform()
      #   ToNode.SetAndObserveTransformNodeID(self.FemurTransform.GetID())
      #   ToNode.HardenTransform()
      myStorageNode = self.model.CreateDefaultStorageNode()
      myStorageNode.SetFileName(self.FilePath+'/FemurTmp.vtk')
      myStorageNode.WriteData(self.model)
      slicer.mrmlScene.RemoveNode(self.model)
      toPoints = slicer.util.arrayFromMarkupsControlPoints(ToNode)
      # for i in range(len(toPoints)):
      #   toPoints[i][0] = -toPoints[i][0]
      #   toPoints[i][1] = -toPoints[i][1]
      try:
        os.remove(self.FilePath+'/test.txt')
      except Exception as e:
        print(e)
      f = open(self.FilePath+'/test.txt', 'w')
      da = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      for i in range(len(toPoints)):
        # for j in range(len(toPoints)):
        f.write(f'{da[i]},{-toPoints[i][0]},{-toPoints[i][1]},{toPoints[i][2]}\n')
      f.close()
      try:
        os.remove(self.FilePath+'/tar.csv')
      except Exception as e:
        print(e)
      os.rename(self.FilePath+'/test.txt', self.FilePath+'/tar.csv')
      command = f'set PATH=' + self.FilePath +'/itk_dll;' + self.FilePath +'/hdf5_dll;%PATH% & '+self.FilePath+'/statismo-fit-surface.exe -v 2.0 -f '+self.FilePath+'/Femur.csv -m '+self.FilePath+'/tar.csv -i '+self.FilePath+'/femurY.h5 -t '+self.FilePath+'/FemurTmp.vtk -w 0.0001 -p -o '+self.FilePath+'/Femur.vtk'
      command=command.replace('-f ', '-f "')
      command =command.replace('-m ','-m "')
      command =command.replace('-i ','-i "')
      command =command.replace('& ','& "')
      command =command.replace('-t ','-t "')
      command = command.replace('-o ', '-o "')
      command =command.replace('.vtk','.vtk"')
      command =command.replace('.csv','.csv"')
      command = command.replace('.exe', '.exe"')
      command = command.replace('.h5', '.h5"')
      os.system(command)
      #os.remove('d:/SliceView/SixView/tar.csv')
      self.model = slicer.util.loadModel(self.FilePath+'/Femur.vtk')


    else:
      # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      #   self.FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '左右镜像')
      #   FemurTrans=np.array([[-1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]])
      #   self.FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
      #   self.model.SetAndObserveTransformNodeID(self.FemurTransform.GetID())
      #   self.model.HardenTransform()
      #   ToNode.SetAndObserveTransformNodeID(self.FemurTransform.GetID())
      #   ToNode.HardenTransform()
      myStorageNode = self.model.CreateDefaultStorageNode()
      myStorageNode.SetFileName(self.FilePath+'/TibiaTmp.vtk')
      myStorageNode.WriteData(self.model)
      slicer.mrmlScene.RemoveNode(self.model)
      toPoints = slicer.util.arrayFromMarkupsControlPoints(ToNode)
      # for i in range(len(toPoints)):
      #   toPoints[i][0] = -toPoints[i][0]
      #   toPoints[i][1] = -toPoints[i][1]
      try:
        os.remove(self.FilePath+'/test.txt')
      except Exception as e:
        print(e)
      f = open(self.FilePath+'/test.txt', 'w')
      da = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      for i in range(len(toPoints)):
        # for j in range(len(toPoints)):
        f.write(f'{da[i]},{toPoints[i][0]},{toPoints[i][1]},{toPoints[i][2]}\n')
      f.close()
      try:
        os.remove(self.FilePath+'/tar.csv')
      except Exception as e:
        print(e)
      os.rename(self.FilePath+'/test.txt', self.FilePath+'/tar.csv')
      command = f'set PATH=' + self.FilePath +'/itk_dll;' + self.FilePath +'/hdf5_dll;%PATH% & '+self.FilePath+'/statismo-fit-surface.exe -v 2.0 -f '+self.FilePath+'/Tibia.csv -m '+self.FilePath+'/tar.csv -i '+self.FilePath+'/tibiaY.h5 -t '+self.FilePath+'/TibiaTmp.vtk -w 0.0001 -p -o '+self.FilePath+'/Tibia.vtk'
      command=command.replace('-f ', '-f "')
      command =command.replace('-m ','-m "')
      command =command.replace('-i ','-i "')
      command =command.replace('& ','& "')
      command =command.replace('-t ','-t "')
      command = command.replace('-o ', '-o "')
      command =command.replace('.vtk','.vtk"')
      command =command.replace('.csv','.csv"')
      command = command.replace('.exe', '.exe"')
      command = command.replace('.h5', '.h5"')
      os.system(command)
      #os.remove('d:/SliceView/SixView/tar.csv')
      self.model = slicer.util.loadModel(self.FilePath+'/Tibia.vtk')
    # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
    #   self.model.SetAndObserveTransformNodeID(self.FemurTransform.GetID())
    #   self.model.HardenTransform()
    #   slicer.mrmlScene.RemoveNode(self.FemurTransform)
    self.model.SetAndObserveTransformNodeID(transNode.GetID())
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'RToL')
      FemurTrans = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
      FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
      if self.ui.centerWidget.currentIndex == 3:
        toolNode=slicer.util.getNode('DianjiToTracker1')
      else:
        toolNode = slicer.util.getNode('TibiaToTracker')

      transNode.SetAndObserveTransformNodeID(FemurTransform.GetID())
      FemurTransform.SetAndObserveTransformNodeID(toolNode.GetID())
    else:
      if self.ui.centerWidget.currentIndex == 3:
        toolNode=slicer.util.getNode('DianjiToTracker1')
      else:
        toolNode = slicer.util.getNode('TibiaToTracker')
      transNode.SetAndObserveTransformNodeID(toolNode.GetID())



    #self.model.HardenTransform()

  def simple_femur(self):
    points = np.loadtxt(self.FilePath + '/simple_femur.txt')
    dis = []
    movNode = slicer.util.getNode('To')
    for j in range(5400):
      landmarkTransform = vtk.vtkLandmarkTransform()
      landmarkTransform.SetModeToRigidBody()
      n = 9
      fix_point = vtk.vtkPoints()
      fix_point.SetNumberOfPoints(n)
      mov_point = vtk.vtkPoints()
      mov_point.SetNumberOfPoints(n)
      mov = slicer.util.arrayFromMarkupsControlPoints(movNode)

      fix = points[j * 9:j * 9 + 9]
      # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      #   for i in range(n):
      #     fix_point.SetPoint(i, -fix[i][0], fix[i][1], fix[i][2])
      #     mov_point.SetPoint(i, mov[i][0], mov[i][1], mov[i][2])
      # else:
      #   for i in range(n):
      #     fix_point.SetPoint(i, fix[i][0], fix[i][1], fix[i][2])
      #     mov_point.SetPoint(i, mov[i][0], mov[i][1], mov[i][2])
      for i in range(n):
        fix_point.SetPoint(i, fix[i][0], fix[i][1], fix[i][2])
        mov_point.SetPoint(i, mov[i][0], mov[i][1], mov[i][2])
      landmarkTransform.SetSourceLandmarks(mov_point)
      landmarkTransform.SetTargetLandmarks(fix_point)
      landmarkTransform.Update()
      trans = slicer.util.arrayFromVTKMatrix(landmarkTransform.GetMatrix())
      for i in range(0, len(mov)):
        l = [mov[i][0], mov[i][1], mov[i][2], 1]
        mov[i] = np.dot(trans, l)[0:3]
      # 计算平均距离
      d = np.linalg.norm(mov - fix)
      dis.append(d)
    print(min(dis), dis.index(min(dis)))
    num = dis.index(min(dis))
    i = int(num / 900)
    num = num % 900
    j = int(num / 180)
    num = num % 180
    k = int(num / 36)
    num = num % 36
    l = int(num / 9)
    num = num % 9
    m = int(num / 3)
    num = num % 3
    n = num

    command = f'set PATH=' + self.FilePath +'/itk_dll;' + self.FilePath +'/hdf5_dll;%PATH% & ' + self.FilePath +'/statismo-sample.exe -i '+self.FilePath + f'/femurY.h5 -p 1:{-2.5 + i / 5 * 5},2:{-2.5 + j / 4 * 5},3:{-2.5 + k / 4 * 5},4:{-2.5 + m / 3 * 5},5:{-2.5 + l / 2 * 5},6:{-2.5 + n / 2 * 5} ' + self.FilePath + '/Femur.vtk'
    command = command.replace('-m ', '-m "')
    command = command.replace(f'6:{-2.5 + n / 2 * 5} ', f'6:{-2.5 + n / 2 * 5} "')
    command = command.replace('-i ', '-i "')
    command = command.replace('& ', '& "')
    command = command.replace('-t ', '-t "')
    command = command.replace('-o ', '-o "')
    command = command.replace('.vtk', '.vtk"')
    command = command.replace('.csv', '.csv"')
    command = command.replace('.exe', '.exe"')
    command = command.replace('.h5', '.h5"')
    os.system(command)
    model=slicer.util.loadModel(self.FilePath + '/Femur.vtk')
    polydata = model.GetPolyData()
    a = polydata.GetNumberOfPoints()
    x1 = np.empty([a, 3])
    for i in range(0, a):
      x1[i] = polydata.GetPoint(i)
      x1[i][0] = -x1[i][0]
      x1[i][1] = -x1[i][1]
    np.savetxt(self.FilePath + "/femur.txt", x1, fmt='%6f')
    slicer.mrmlScene.RemoveNode(model)
    num = dis.index(min(dis))
    #将拟合所用点列替换为最佳模型所对应的值

    frompoints=points[num * 9:num * 9 + 9]
    try:
      os.remove(self.FilePath + '/test.txt')
    except Exception as e:
      print(e)
    f = open(self.FilePath + '/test.txt', 'w')
    da = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(len(frompoints)):
      # for j in range(len(toPoints)):
      f.write(f'{da[i]},{-frompoints[i][0]},{-frompoints[i][1]},{frompoints[i][2]}\n')
    f.close()
    try:
      os.remove(self.FilePath + '/Femur.csv')
    except Exception as e:
      print(e)
    os.rename(self.FilePath + '/test.txt', self.FilePath + '/Femur.csv')
    # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
    #   for i in range(len(frompoints)):
    #     frompoints[i][0]=-frompoints[i][0]
    return frompoints
    
  def simple_tibia(self):
    points = np.loadtxt(self.FilePath + '/simple_tibia.txt')
    dis = []
    movNode = slicer.util.getNode('To')
    for j in range(5400):
      landmarkTransform = vtk.vtkLandmarkTransform()
      landmarkTransform.SetModeToRigidBody()
      n = 4
      fix_point = vtk.vtkPoints()
      fix_point.SetNumberOfPoints(n)
      mov_point = vtk.vtkPoints()
      mov_point.SetNumberOfPoints(n)
      mov = slicer.util.arrayFromMarkupsControlPoints(movNode)
      mov=mov[0:4]
      fix = points[j * 4:j * 4 + 4]
      # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      #   for i in range(n):
      #     fix_point.SetPoint(i, -fix[i][0], fix[i][1], fix[i][2])
      #     mov_point.SetPoint(i, mov[i][0], mov[i][1], mov[i][2])

      for i in range(n):
        fix_point.SetPoint(i, fix[i][0], fix[i][1], fix[i][2])
        mov_point.SetPoint(i, mov[i][0], mov[i][1], mov[i][2])
      landmarkTransform.SetSourceLandmarks(mov_point)
      landmarkTransform.SetTargetLandmarks(fix_point)
      landmarkTransform.Update()
      trans = slicer.util.arrayFromVTKMatrix(landmarkTransform.GetMatrix())
      for i in range(0, len(mov)):
        l = [mov[i][0], mov[i][1], mov[i][2], 1]
        mov[i] = np.dot(trans, l)[0:3]
      # 计算平均距离
      d = np.linalg.norm(mov - fix)
      dis.append(d)
    print(min(dis), dis.index(min(dis)))
    num = dis.index(min(dis))
    i = int(num / 900)
    num = num % 900
    j = int(num / 180)
    num = num % 180
    k = int(num / 36)
    num = num % 36
    l = int(num / 9)
    num = num % 9
    m = int(num / 3)
    num = num % 3
    n = num

    command = f'set PATH=' + self.FilePath +'/itk_dll;' + self.FilePath +'/hdf5_dll;%PATH% & ' + self.FilePath +'/statismo-sample.exe -i '+self.FilePath + f'/tibiaY.h5 -p 1:{-2.5 + i / 5 * 5},2:{-2.5 + j / 4 * 5},3:{-2.5 + k / 4 * 5},4:{-2.5 + m / 3 * 5},5:{-2.5 + l / 2 * 5},6:{-2.5 + n / 2 * 5} ' + self.FilePath + '/Tibia.vtk'
    command = command.replace('-m ', '-m "')
    command = command.replace(f'6:{-2.5 + n / 2 * 5} ', f'6:{-2.5 + n / 2 * 5} "')
    command = command.replace('-i ', '-i "')
    command = command.replace('& ', '& "')
    command = command.replace('-t ', '-t "')
    command = command.replace('-o ', '-o "')
    command = command.replace('.vtk', '.vtk"')
    command = command.replace('.csv', '.csv"')
    command = command.replace('.exe', '.exe"')
    command = command.replace('.h5', '.h5"')
    os.system(command)
    model=slicer.util.loadModel(self.FilePath + '/Tibia.vtk')
    polydata = model.GetPolyData()
    a = polydata.GetNumberOfPoints()
    x1 = np.empty([a, 3])
    for i in range(0, a):
      x1[i] = polydata.GetPoint(i)
      x1[i][0] = -x1[i][0]
      x1[i][1] = -x1[i][1]
    np.savetxt(self.FilePath + "/tibia.txt", x1, fmt='%6f')
    slicer.mrmlScene.RemoveNode(model)
    num = dis.index(min(dis))
    #将拟合所用点列替换为最佳模型所对应的值

    frompoints=points[num * 4:num * 4 + 4]
    try:
      os.remove(self.FilePath + '/test.txt')
    except Exception as e:
      print(e)
    f = open(self.FilePath + '/test.txt', 'w')
    da = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in range(len(frompoints)):
      # for j in range(len(toPoints)):
      f.write(f'{da[i]},{frompoints[i][0]},{frompoints[i][1]},{frompoints[i][2]}\n')
    f.close()
    try:
      os.remove(self.FilePath + '/Tibia.csv')
    except Exception as e:
      print(e)
    os.rename(self.FilePath + '/test.txt', self.FilePath + '/Tibia.csv')
    # if slicer.modules.NoImageWelcomeWidget.judge == 'L':
    #   for i in range(len(frompoints)):
    #     frompoints[i][0]=-frompoints[i][0]
    return frompoints

  def ssm_nihe_n(self,Topoints):
    if self.ui.centerWidget.currentIndex == 3:
      command = f'set PATH=' + self.FilePath +'/itk_dll;' + self.FilePath +'/hdf5_dll;%PATH% & '+self.FilePath+'/statismo-fit-surface.exe -v 2.0 -f '+self.FilePath+'/Femur.csv -m '+self.FilePath+'/tar.csv -i '+self.FilePath+'/femurY.h5 -t '+self.FilePath+'/Femur.vtk -w 0.0001 -p -o '+self.FilePath+'/Femur.vtk'
      command=command.replace('-f ', '-f "')
      command =command.replace('-m ','-m "')
      command =command.replace('-i ','-i "')
      command =command.replace('& ','& "')
      command =command.replace('-t ','-t "')
      command = command.replace('-o ', '-o "')
      command =command.replace('.vtk','.vtk"')
      command =command.replace('.csv','.csv"')
      command = command.replace('.exe', '.exe"')
      command = command.replace('.h5', '.h5"')
      os.system(command)
      self.model = slicer.util.loadModel(self.FilePath + '/Femur.vtk')
      polydata = self.model.GetPolyData()
      a = polydata.GetNumberOfPoints()
      x1 = np.empty([a, 3])
      for i in range(0, a):
        x1[i] = polydata.GetPoint(i)
      target_new = Topoints
      self.data = x1

      for i in range(len(target_new)):
        idx = self.panduan(self.data, target_new[i])
        # print(idx)
        self.data = self.move(self.data, idx, target_new[i])
      data1 = np.empty([len(self.data), 3])
      for i in range(0, len(self.data)):
        data1[i] = np.array([-self.data[i][0], -self.data[i][1], self.data[i][2]])
      self.remesh(data1)
      slicer.mrmlScene.RemoveNode(self.model)
      self.model = slicer.util.loadModel(self.FilePath + '/Femur.vtk')
    else:
      command = f'set PATH=' + self.FilePath +'/itk_dll;' + self.FilePath +'/hdf5_dll;%PATH% & ' + self.FilePath + '/statismo-fit-surface.exe -v 2.0 -f ' + self.FilePath + '/Tibia.csv -m ' + self.FilePath + '/tar.csv -i ' + self.FilePath + '/tibiaY.h5 -t ' + self.FilePath + '/Tibia.vtk -w 0.0001 -p -o ' + self.FilePath + '/Tibia.vtk'
      command = command.replace('-f ', '-f "')
      command = command.replace('-m ', '-m "')
      command = command.replace('-i ', '-i "')
      command = command.replace('& ', '& "')
      command = command.replace('-t ', '-t "')
      command = command.replace('-o ', '-o "')
      command = command.replace('.vtk', '.vtk"')
      command = command.replace('.csv', '.csv"')
      command = command.replace('.exe', '.exe"')
      command = command.replace('.h5', '.h5"')
      os.system(command)
      self.model = slicer.util.loadModel(self.FilePath + '/Tibia.vtk')
      polydata = self.model.GetPolyData()
      a = polydata.GetNumberOfPoints()
      x1 = np.empty([a, 3])
      for i in range(0, a):
        x1[i] = polydata.GetPoint(i)
      target_new = Topoints
      self.data = x1

      for i in range(len(target_new)):
        idx = self.panduan(self.data, target_new[i])
        # print(idx)
        self.data = self.move(self.data, idx, target_new[i])
      data1 = np.empty([len(self.data), 3])
      for i in range(0, len(self.data)):
        data1[i] = np.array([-self.data[i][0], -self.data[i][1], self.data[i][2]])
      self.remesh(data1)
      slicer.mrmlScene.RemoveNode(self.model)
      self.model = slicer.util.loadModel(self.FilePath + '/Tibia.vtk')
  
  #确认函数
  def onConfirm2(self):
    # self.ui.ForwardToolButton.setEnabled(True)
    # 将精拟合所用的点置于股骨头坐标系，方便拟合
    self.onGuGuTouConfirm()#确认股骨头球心
    polydata = self.model.GetPolyData()
    a = polydata.GetNumberOfPoints()
    x1 = np.empty([a, 3])
    for i in range(0, a):
      x1[i] = polydata.GetPoint(i)
    ToNode = slicer.util.getNode('To')
    Topoints = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      ToNode.RemoveAllControlPoints()
      for i in range(len(Topoints)):
        ToNode.AddControlPoint(-Topoints[i][0], Topoints[i][1], Topoints[i][2])
    # ToNode.RemoveAllControlPoints()
    # if self.ui.centerWidget.currentIndex == 3:
    #   p1=np.loadtxt('E:/mesh_points.txt')
    # else:
    #   p1=np.loadtxt('E:/t2.txt')
    # for i in range(len(p1)):
    #   ToNode.AddControlPoint(p1[i])
    Topoints = slicer.util.arrayFromMarkupsControlPoints(ToNode)
    if self.ui.centerWidget.currentIndex == 3:
      transNode = slicer.util.getNode('FromToTo_femur')
    else:
      transNode = slicer.util.getNode('FromToTo_tibia')
    trans = slicer.util.arrayFromTransformMatrix(transNode)
    trans_ni = np.linalg.inv(trans)
    for i in range(0, len(Topoints)):
      l = [Topoints[i][0], Topoints[i][1], Topoints[i][2], 1]
      Topoints[i] = np.dot(trans_ni, l)[0:3]
    # target_new = [[9.914172,-6.626008,42.820110]]
    target_new = Topoints
    self.data = x1
    #for j in range(0,3):
    # idx=[]
    # for i in range(len(target_new)):
    #   idx.append(self.panduan(self.data, target_new[i]))
      # print(idx)


    # landmarkTransform = vtk.vtkLandmarkTransform()
    # landmarkTransform.SetModeToRigidBody()
    # n = len(target_new)
    # fix_point = vtk.vtkPoints()
    # fix_point.SetNumberOfPoints(n)
    # mov_point = vtk.vtkPoints()
    # mov_point.SetNumberOfPoints(n)
    # mov=self.data[idx]
    # fix=target_new
    # for i in range(n):
    #   fix_point.SetPoint(i, fix[i][0], fix[i][1], fix[i][2])
    #   mov_point.SetPoint(i, mov[i][0], mov[i][1], mov[i][2])
    # landmarkTransform.SetSourceLandmarks(mov_point)
    # landmarkTransform.SetTargetLandmarks(fix_point)
    # landmarkTransform.Update()
    # trans = slicer.util.arrayFromVTKMatrix(landmarkTransform.GetMatrix())
    # for i in range(0, len(self.data)):
    #   l = [self.data[i][0], self.data[i][1], self.data[i][2], 1]
    #   self.data[i] = np.dot(trans, l)[0:3]


    fiducialsPolyData = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    for i in range(len(target_new)):
      points.InsertNextPoint(target_new[i])

    tempPolyData = vtk.vtkPolyData()
    tempPolyData.SetPoints(points)
    vertex = vtk.vtkVertexGlyphFilter()
    vertex.SetInputData(tempPolyData)
    vertex.Update()
    fiducialsPolyData.ShallowCopy(vertex.GetOutput())

    icpTransform = vtk.vtkIterativeClosestPointTransform()
    icpTransform.SetSource(fiducialsPolyData)
    icpTransform.SetTarget(polydata)
    icpTransform.GetLandmarkTransform().SetModeToRigidBody()
    icpTransform.SetMaximumNumberOfIterations(100)
    icpTransform.Modified()
    icpTransform.Update()
    trans_ni = slicer.util.arrayFromVTKMatrix(icpTransform.GetMatrix())
    trans = np.linalg.inv(trans_ni)
    print('面配准矩阵',trans)
    for i in range(0, len(self.data)):
      l = [self.data[i][0], self.data[i][1], self.data[i][2], 1]
      self.data[i] = np.dot(trans, l)[0:3]


    for i in range(len(target_new)):
      idx=self.panduan(self.data, target_new[i])
      self.data = self.move(self.data, idx, target_new[i])
    data1 = np.empty([len(self.data), 3])
    for i in range(0, len(self.data)):
      data1[i] = np.array([-self.data[i][0], -self.data[i][1], self.data[i][2]])
    self.remesh(data1)
    #多次拟合
    # self.ssm_nihe_n(Topoints)
    # self.ssm_nihe_n(Topoints)
    slicer.mrmlScene.RemoveNode(self.model)
    if self.ui.centerWidget.currentIndex == 3 :
      self.model=slicer.util.loadModel(self.FilePath+'/Femur.vtk')
      self.model.SetName('Femur')
      self.model.SetAndObserveTransformNodeID(transNode.GetID())
      self.model.HardenTransform()
      if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        slicer.mrmlScene.RemoveNode(slicer.util.getNode('RToL'))
        FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'RToL')
        FemurTrans = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
        self.model.SetAndObserveTransformNodeID(FemurTransform.GetID())
        self.model.HardenTransform()
        slicer.mrmlScene.RemoveNode(FemurTransform)
        print('jingnihe')
        #镜像转化代码无效，重复执行一次
        slicer.mrmlScene.RemoveNode(self.model)
        transNode = slicer.util.getNode('FromToTo_femur')
        self.model = slicer.util.loadModel(self.FilePath+'/Femur.vtk')
        self.model.SetName('Femur')
        self.model.SetAndObserveTransformNodeID(transNode.GetID())
        self.model.HardenTransform()
        # slicer.mrmlScene.RemoveNode(slicer.util.getNode('RToL'))
        FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'RToL')
        FemurTrans = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
        self.model.SetAndObserveTransformNodeID(FemurTransform.GetID())
        self.model.HardenTransform()
        slicer.mrmlScene.RemoveNode(FemurTransform)
        self.EtctMove('Femur','DianjiToTracker1')
      else:
        self.NodeMove('Femur','DianjiToTracker1')

    else:
      self.model = slicer.util.loadModel(self.FilePath+'/Tibia.vtk')
      self.model.SetName('Tibia')
      self.model.SetAndObserveTransformNodeID(transNode.GetID())
      self.model.HardenTransform()
      if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        slicer.mrmlScene.RemoveNode(slicer.util.getNode('RToL'))
        FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'RToL')
        FemurTrans = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
        self.model.SetAndObserveTransformNodeID(FemurTransform.GetID())
        self.model.HardenTransform()
        slicer.mrmlScene.RemoveNode(FemurTransform)
        slicer.mrmlScene.RemoveNode(self.model)
        transNode = slicer.util.getNode('FromToTo_tibia')
        self.model = slicer.util.loadModel(self.FilePath+'/Tibia.vtk')
        self.model.SetName('Tibia')
        self.model.SetAndObserveTransformNodeID(transNode.GetID())
        self.model.HardenTransform()
        # slicer.mrmlScene.RemoveNode(slicer.util.getNode('RToL'))
        FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'RToL')
        FemurTrans = np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
        self.model.SetAndObserveTransformNodeID(FemurTransform.GetID())
        self.model.HardenTransform()
        slicer.mrmlScene.RemoveNode(FemurTransform)
        self.EtctMove('Tibia','TibiaToTracker')
      else:
        self.NodeMove('Tibia','TibiaToTracker')
      slicer.util.getNode('NeedleModel').SetDisplayVisibility(False)
      slicer.util.getNode('From').SetDisplayVisibility(False)
      slicer.util.getNode('To').SetDisplayVisibility(False)
      #添加计算所需的点。
      #self.buildPointsInFemur()
    self.Smooth_Model(self.model)
    print("aaaa",self.ui.centerWidget.currentIndex)
    #股骨配准跳转至胫骨配准
    if self.ui.centerWidget.currentIndex == 3:
      print("骨配准跳转至胫骨配准")
      self.gugu2jinggu()
      return
    #胫骨配准跳转至膝关节评估
    if self.ui.centerWidget.currentIndex == 4:
      print("胫骨配准跳转至膝关节评估")
      self.jinggu2pinggu()
      return



  def CaculateClosedPoint(self, surface_World, point_World):
    distanceFilter = vtk.vtkImplicitPolyDataDistance()
    distanceFilter.SetInput(surface_World)
    closestPointOnSurface_World = np.zeros(3)
    closestPointDistance = distanceFilter.EvaluateFunctionAndGetClosestPoint(point_World, closestPointOnSurface_World)
    return closestPointDistance,closestPointOnSurface_World

  def Smooth_Model(self,model):
    import SurfaceToolbox
    slicer.modules.surfacetoolbox.widgetRepresentation()
    slicer.modules.SurfaceToolboxWidget._parameterNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScriptedModuleNode")
    slicer.modules.SurfaceToolboxWidget.setParameterNode(slicer.modules.SurfaceToolboxWidget._parameterNode)
    slicer.modules.SurfaceToolboxWidget._parameterNode.SetNodeReferenceID("inputModel", model.GetID())
    slicer.modules.SurfaceToolboxWidget._parameterNode.SetNodeReferenceID("outputModel", model.GetID())
    slicer.modules.SurfaceToolboxWidget._parameterNode.SetParameter("smoothing", "true")
    slicer.modules.SurfaceToolboxWidget._parameterNode.SetParameter("smoothingMethod", "Laplace")
    slicer.modules.SurfaceToolboxWidget._parameterNode.SetParameter("smoothingLaplaceIterations", "11")
    slicer.modules.SurfaceToolboxWidget._parameterNode.SetParameter("smoothingLaplaceRelaxation", "0.1")
    slicer.modules.SurfaceToolboxWidget.onApplyButton()
    slicer.mrmlScene.RemoveNode(slicer.modules.SurfaceToolboxWidget._parameterNode)


  def onHPoint(self):
    try:
      f=slicer.util.getNode('H点')
      slicer.mrmlScene.RemoveNode(f)
    except:
      pass
    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'H点')
    probeToTransformNode = slicer.util.getNode("StylusTipToStylus")
    if self.VRstate:
      f.AddControlPoint(self.vrPoint)
    else:
      slicer.modules.fiducialregistrationwizard.logic().AddFiducial(probeToTransformNode, f)
    
    transformNode = slicer.util.getNode('DianjiToTracker1')
    f.SetAndObserveTransformNodeID(transformNode.GetID())
    self.PointMove('H点','DianjiToTracker1')
    
  def onGuGuTou(self):
    name=[]
    nodes=slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
    for i in range(len(nodes)):
      node=nodes[i]
      name.append(node.GetName())
    if '球心拟合' in name:
      f=slicer.util.getNode('球心拟合')

    else:
      f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '球心拟合')
      transformNode = slicer.util.getNode('DianjiToTracker1')
      f.SetAndObserveTransformNodeID(transformNode.GetID())


    probeToTransformNode = slicer.util.getNode("StylusTipToStylus")
    if self.VRstate:
      f.AddControlPoint(self.vrPoint)
    else:
      slicer.modules.fiducialregistrationwizard.logic().AddFiducial(probeToTransformNode, f)
    self.PointMove('球心拟合', 'DianjiToTracker1')
    Number = ["⑳", "⑲", "⑱", "⑰", "⑯", "⑮", "⑭", "⑬", "⑫", "⑪", "⑩", "⑨", "⑧", "⑦", "⑥", "⑤", "④", "③", "②", "①"]
    num = f.GetNumberOfControlPoints()

    self.ui.femurPoint16Label.setText(Number[19-num%20])
  
  def onGuGuTouConfirm(self):
    f=slicer.util.getNode('球心拟合')
    points=slicer.util.arrayFromMarkupsControlPoints(f)
    slicer.mrmlScene.RemoveNode(f)
    points = points.astype(np.float64)  # 防止溢出
    num_points = points.shape[0]
    print(num_points)
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    x_avr = sum(x) / num_points
    y_avr = sum(y) / num_points
    z_avr = sum(z) / num_points
    xx_avr = sum(x * x) / num_points
    yy_avr = sum(y * y) / num_points
    zz_avr = sum(z * z) / num_points
    xy_avr = sum(x * y) / num_points
    xz_avr = sum(x * z) / num_points
    yz_avr = sum(y * z) / num_points
    xxx_avr = sum(x * x * x) / num_points
    xxy_avr = sum(x * x * y) / num_points
    xxz_avr = sum(x * x * z) / num_points
    xyy_avr = sum(x * y * y) / num_points
    xzz_avr = sum(x * z * z) / num_points
    yyy_avr = sum(y * y * y) / num_points
    yyz_avr = sum(y * y * z) / num_points
    yzz_avr = sum(y * z * z) / num_points
    zzz_avr = sum(z * z * z) / num_points

    A = np.array([[xx_avr - x_avr * x_avr, xy_avr - x_avr * y_avr, xz_avr - x_avr * z_avr],
                  [xy_avr - x_avr * y_avr, yy_avr - y_avr * y_avr, yz_avr - y_avr * z_avr],
                  [xz_avr - x_avr * z_avr, yz_avr - y_avr * z_avr, zz_avr - z_avr * z_avr]])
    b = np.array([xxx_avr - x_avr * xx_avr + xyy_avr - x_avr * yy_avr + xzz_avr - x_avr * zz_avr,
                  xxy_avr - y_avr * xx_avr + yyy_avr - y_avr * yy_avr + yzz_avr - y_avr * zz_avr,
                  xxz_avr - z_avr * xx_avr + yyz_avr - z_avr * yy_avr + zzz_avr - z_avr * zz_avr])
    # print(A, b)
    b = b / 2
    center = np.linalg.solve(A, b)
    x0 = center[0]
    y0 = center[1]
    z0 = center[2]
    r2 = xx_avr - 2 * x0 * x_avr + x0 * x0 + yy_avr - 2 * y0 * y_avr + y0 * y0 + zz_avr - 2 * z0 * z_avr + z0 * z0
    r = r2 ** 0.5
    print(center, r)
    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨头球心')
    transformNode = slicer.util.getNode('DianjiToTracker1')
    f.SetAndObserveTransformNodeID(transformNode.GetID())
    f.AddControlPoint(center[0],center[1],center[2])
    f.SetDisplayVisibility(False)
    h=slicer.util.getNode('H点')
    h.SetDisplayVisibility(False)


  #配准过程中调用的函数
  def distance(self, p1, p2):
    p3 = p1 - p2
    d = np.sqrt(np.dot(p3, p3))
    return d

  def move(self, data, i, target):
    n = target - data[i]
    r = 30
    point_index = []
    point_d = []
    for j in range(len(data)):
      d = self.distance(data[j], data[i])
      if d < r:
        point_index.append(j)
        point_d.append(d)
    for j in range(len(point_index)):
      data[point_index[j]] = (1 - point_d[j] / r) * n + data[point_index[j]]
    return data

  def panduan(self, old_target, target):
    hh = {}
    for i in range(len(old_target)):
      d = self.distance(old_target[i], target)
      # print(d)
      hh[i] = d
    return int(min(hh, key=hh.get))

  def remesh(self, data):
    try:
      if self.ui.centerWidget.currentIndex == 3 :
        os.remove(self.FilePath+'/Femur.vtk')
      else:
        os.remove(self.FilePath+'/Tibia.vtk')
    except Exception as e:
      print(e)
    hhh = data.tolist()
    if self.ui.centerWidget.currentIndex == 3 :
      mesh = open(self.FilePath+'/mesh_femur.txt').readlines()
    else:
      mesh = open(self.FilePath+'/mesh_tibia.txt').readlines()
    for i in range(len(mesh)):
      hhh.append(mesh[i].replace('\n', ''))
    f = open(self.FilePath+'/out.txt', 'a+')
    f.write('''# vtk DataFile Version 3.0
            vtk output
            ASCII
            DATASET POLYDATA
            POINTS 10000 float''')
    for i in range(len(hhh)):
      # print(f"\n{str(hhh[i]).replace(',', ' ').replace('[', '').replace(']', '')}")
      f.write(f"\n{str(hhh[i]).replace(',', ' ').replace('[', '').replace(']', '')}")
    f.close()
    if self.ui.centerWidget.currentIndex == 3 :
      os.rename(self.FilePath+'/out.txt', self.FilePath+'/Femur.vtk')
    else:
      os.rename(self.FilePath+'/out.txt', self.FilePath+'/Tibia.vtk')

  #-----------一些初始化的函数---------------------------------------------
  # def FemurButtonChecked(self,button):
  #   self.ui.Parameter.setChecked(False)
  #   self.ui.Adjustment.setChecked(False)
  #   self.ui.ViewChoose.setChecked(False)
  #   self.ui.Reset.setChecked(False)
  #   self.ui.ForceLine.setChecked(False)
  #   if button == None:
  #     self.HideAll()
  #   else:
  #     button.setChecked(True)

  # def TibiaButtonChecked(self,button):
  #   self.ui.Parameter2.setChecked(False)
  #   self.ui.Adjustment2.setChecked(False)
  #   self.ui.ViewChoose2.setChecked(False)
  #   self.ui.ReSet2.setChecked(False)
  #   self.ui.ForceLine2.setChecked(False)
  #   if button == None:
  #       self.HideAll()
  #   else:
  #       button.setChecked(True)

  # def ReportButtonChecked(self,button):
  #   self.ui.JieTu.setChecked(False)
  #   self.ui.CTReport.setChecked(False)
  #   self.ui.MRIReport.setChecked(False)
  #   if button == None:
  #       self.HideAll()
  #   else:
  #       button.setChecked(True)
  
  # def NavigationButtonChecked(self,button):
  #   self.ui.DriveJZ.setChecked(False)
  #   self.ui.FemurQG.setChecked(False)
  #   self.ui.TibiaQG.setChecked(False)
  #   if button == None:
  #       self.HideAll()
  #   else:      
  #       button.setChecked(True)


  #模型及点随工具而动
  def NodeMove(self, modelName, transName):
    modelNode = slicer.util.getNode(modelName)
    transNode = slicer.util.getNode(transName)
    Ftrans3 = slicer.util.arrayFromTransformMatrix(transNode)
    Ftrans3_ni = np.linalg.inv(Ftrans3)
    Transform_tmp = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'trans_tmp')
    Transform_tmp.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans3_ni))
    modelNode.SetAndObserveTransformNodeID(Transform_tmp.GetID())
    modelNode.HardenTransform()
    modelNode.SetAndObserveTransformNodeID(transNode.GetID())
    slicer.mrmlScene.RemoveNode(Transform_tmp)

  def PointMove(self, pointName, transName):
    pointNode = slicer.util.getNode(pointName)
    transNode = slicer.util.getNode(transName)
    Ftrans3 = slicer.util.arrayFromTransformMatrix(transNode)
    Ftrans3_ni = np.linalg.inv(Ftrans3)
    points = slicer.util.arrayFromMarkupsControlPoints(pointNode)
    l = [points[-1][0], points[-1][1], points[-1][2], 1]
    mov = np.dot(Ftrans3_ni, l)[0:3]
    pointNode.RemoveNthControlPoint(len(points)-1)
    pointNode.AddControlPoint(mov)

  def EtctMove(self, nodeName, transName):
    pointNode = slicer.util.getNode(nodeName)
    transNode = slicer.util.getNode(transName)
    pointNode.SetAndObserveTransformNodeID(transNode.GetID())

  def addAxisFemur(self):
    o = [0, 0, 0]
    z = [0, 0, 1]
    y = [0, 1, 0]
    x = [1, 0, 0]

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Femur_ZAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(z)
    Femur_ZAxis = slicer.util.getNode('变换_1')
    f.SetAndObserveTransformNodeID(Femur_ZAxis.GetID())
    f.SetDisplayVisibility(False)


    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Femur_XAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(x)
    Femur_XAxis = slicer.util.getNode('变换_1')
    f.SetAndObserveTransformNodeID(Femur_XAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Femur_ZJtAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(z)
    Femur_ZJtAxis = slicer.util.getNode('变换_R')
    f.SetAndObserveTransformNodeID(Femur_ZJtAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Femur_YJtAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(y)
    Femur_ZJtAxis = slicer.util.getNode('变换_R')
    f.SetAndObserveTransformNodeID(Femur_ZJtAxis.GetID())
    f.SetDisplayVisibility(False)

  def addAxisTibia(self):
    o = [0, 0, 0]
    x=[1,0,0]
    z = [0, 0, 1]
    y = [0, 1, 0]

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_ZAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(z)
    Tibia_ZAxis = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_ZAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_XAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(x)
    Tibia_XAxis = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_XAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_YAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(y)
    Tibia_YAxis = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_YAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_ZJtAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(z)
    Tibia_ZJtAxis = slicer.util.getNode('变换_约束')
    f.SetAndObserveTransformNodeID(Tibia_ZJtAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_YZPlane')
    f.AddControlPoint(o)
    f.AddControlPoint(y)
    f.AddControlPoint(z)
    Tibia_YZPlane = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_YZPlane.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_XZPlane')
    f.AddControlPoint(o)
    f.AddControlPoint(x)
    f.AddControlPoint(z)
    Tibia_XZPlane = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_XZPlane.GetID())
    f.SetDisplayVisibility(False)

  # def buildPointsInFemur(self):

  #   line_outside = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", 'line_outside')
  #   l1 = slicer.util.getNode('外侧后髁')
  #   l2 = slicer.util.getNode('外侧远端')
  #   p1 = slicer.util.arrayFromMarkupsControlPoints(l1)[0]
  #   p2 = slicer.util.arrayFromMarkupsControlPoints(l2)[0]
  #   line_outside.AddControlPoint(p1)
  #   line_outside.AddControlPoint(p2)
  #   transNode = slicer.util.getNode('DianjiToTracker1')
  #   line_outside.SetAndObserveTransformNodeID(transNode.GetID())
  #   line_outside.SetCurveTypeToShortestDistanceOnSurface(slicer.util.getNode('Femur'))
  #   line_outside.ResampleCurveSurface(2, slicer.util.getNode('Femur'))

  #   self.points_outside = slicer.util.arrayFromMarkupsControlPoints(line_outside)
  #   line_inside = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", 'line_inside')
  #   l1 = slicer.util.getNode('内侧后髁')
  #   l2 = slicer.util.getNode('内侧远端')
  #   p1 = slicer.util.arrayFromMarkupsControlPoints(l1)[0]
  #   p2 = slicer.util.arrayFromMarkupsControlPoints(l2)[0]
  #   line_inside.AddControlPoint(p1)
  #   line_inside.AddControlPoint(p2)
  #   line_inside.SetAndObserveTransformNodeID(transNode.GetID())
  #   line_inside.SetCurveTypeToShortestDistanceOnSurface(slicer.util.getNode('Femur'))
  #   line_inside.ResampleCurveSurface(2, slicer.util.getNode('Femur'))
  #   self.points_inside = slicer.util.arrayFromMarkupsControlPoints(line_inside)
  #   slicer.mrmlScene.RemoveNode(line_outside)
  #   slicer.mrmlScene.RemoveNode(line_inside)

  # 计算当前最低值及角度
  def caculateLowPoint(self, unusedArg1=None, unusedArg2=None, unusedArg3=None):
    #TibiaJGM = self.GetTransPoint('胫骨截骨面')
    ras1, ras2, ras3, ras4 = [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]
    ras5, ras6 = [0, 0, 0], [0, 0, 0]
    slicer.util.getNode('内侧高点').GetNthControlPointPositionWorld(0, ras1)
    slicer.util.getNode('外侧高点').GetNthControlPointPositionWorld(0, ras2)
    slicer.util.getNode('内侧远端').GetNthControlPointPositionWorld(0, ras3)
    slicer.util.getNode('外侧远端').GetNthControlPointPositionWorld(0, ras4)
    slicer.util.getNode('内侧后髁').GetNthControlPointPositionWorld(0, ras5)
    slicer.util.getNode('外侧后髁').GetNthControlPointPositionWorld(0, ras6)

    
    Femur_ZAxis_Z = self.caculateTouYingNorml('Femur_ZAxis', 'Tibia_YZPlane')
    Tibia_ZAxis = self.GetNorlm('Tibia_ZAxis')
    #quxiAngle = self.angle(Femur_ZAxis_Z, Tibia_ZAxis)
    quxiAngle=self.Angle(Femur_ZAxis_Z, Tibia_ZAxis)
    

    Tibia_XAxis = self.GetNorlm('Tibia_XAxis')
    Tibia_YAxis = self.GetNorlm('Tibia_YAxis')
    Femur_ZAxis = self.GetNorlm('Femur_ZAxis')
    ifzf1=np.dot(Tibia_YAxis,Femur_ZAxis)
    print("ifzf1",ifzf1)
    if (ifzf1<0):
      quxiAngle=-quxiAngle

    Femur_XAxis_Z = self.caculateTouYingNorml('Femur_ZAxis', 'Tibia_YZPlane')
    waifanAngle=float(self.angle(Femur_XAxis_Z, Femur_ZAxis))
    if(np.dot(Tibia_XAxis,Femur_ZAxis)>0):
      waifanAngle=-waifanAngle



    if waifanAngle <-14 :
      waifanAngle=-14


    if waifanAngle >14:
      waifanAngle=14

    if quxiAngle <-14 :
      quxiAngle=-14


    if quxiAngle >130:
      quxiAngle=130

    self.currentY=float(waifanAngle)
    self.currentX=float(quxiAngle)
    print("quxiAngle",quxiAngle)
    print("waifanAngle",waifanAngle)
    
    #调用腿旋转UI
    self.currentY = round(self.currentY,1)
    self.currentX = round(self.currentX,1)
    self.leg_rotation.setRotation(self.currentX)
    self.leg_rotation1.setRotation(self.currentX)
    self.leg_rotation2.setRotation(self.currentX)
    self.leg_rotation_cut.setRotation(self.currentX)
    #调用记录最大最小值UI
    self.flipcorner.OnhhhMoved(self.currentX)
    self.flipcorner1.OnhhhMoved(self.currentX)
    self.flipcorner2.OnhhhMoved(self.currentX)
    self.flipcorner.OnvvvMoved(self.currentY)
    self.flipcorner1.OnvvvMoved(self.currentY)
    self.flipcorner2.OnvvvMoved(self.currentY)

    if(-1<self.currentX<1):#伸直时计算伸直间隙
      shenzhi_neicejianxi=np.sqrt(np.dot(np.array(ras1)-ras3,np.array(ras1)-ras3))
      shenzhi_waicejianxi=np.sqrt(np.dot(np.array(ras2)-ras4,np.array(ras2)-ras4))
      shenzhi_neicejianxi = round(shenzhi_neicejianxi,1)
      shenzhi_waicejianxi = round(shenzhi_waicejianxi,1)
      #膝关节评估0°内外翻距离UI
      #伸直内侧
      self.flipcorner_0_90.on_l_r_changed(shenzhi_neicejianxi)
      self.flipcorner_0_90_1.on_l_r_changed(shenzhi_neicejianxi)
      self.flipcorner_0_90_2.on_l_r_changed(shenzhi_neicejianxi)
      self.B1 = shenzhi_neicejianxi
      #伸直外侧
      self.flipcorner_0_90.on_l_l_changed(shenzhi_waicejianxi)
      self.flipcorner_0_90_1.on_l_l_changed(shenzhi_waicejianxi)
      self.flipcorner_0_90_2.on_l_l_changed(shenzhi_waicejianxi)
      self.A1 = shenzhi_waicejianxi
      #切割界面0°内外翻距离UI
      self.flipcorner_one.on_l_r_changed(shenzhi_neicejianxi)
      self.flipcorner_one.on_l_l_changed(shenzhi_waicejianxi)
      #切割界面记录0°内外翻角UI
      self.flipcorner_0.OnhhhMoved(self.currentX)
      self.flipcorner_0.OnvvvMoved(self.currentY)

    if(89<self.currentX<91):#屈膝时计算屈膝间隙
      quxi_neicejianxi=np.sqrt(np.dot(np.array(ras1)-ras5,np.array(ras1)-ras5))
      quxi_waicejianxi=np.sqrt(np.dot(np.array(ras2)-ras6,np.array(ras2)-ras6))
      quxi_neicejianxi = round(quxi_neicejianxi,1)
      quxi_waicejianxi = round(quxi_waicejianxi,1)
      #膝关节评估90°内外翻距离UI
      #屈膝内侧
      self.flipcorner_0_90.on_r_r_changed(quxi_neicejianxi)
      self.flipcorner_0_90_1.on_r_r_changed(quxi_neicejianxi)
      self.flipcorner_0_90_2.on_r_r_changed(quxi_neicejianxi)
      self.D1 = quxi_neicejianxi
      #屈膝外侧
      self.flipcorner_0_90.on_r_l_changed(quxi_waicejianxi)
      self.flipcorner_0_90_1.on_r_l_changed(quxi_waicejianxi)
      self.flipcorner_0_90_2.on_r_l_changed(quxi_waicejianxi)
      self.C1 = quxi_waicejianxi
      #切割界面90°内外翻距离UI
      self.flipcorner_one.on_l_r_changed(quxi_neicejianxi)
      self.flipcorner_one.on_l_l_changed(quxi_waicejianxi)
    time.sleep(0.05)
    
    
  def caculaleQuxiAndeWaifanInTiaozheng(self):

    Femur_ZAxis_Z = self.caculateTouYingNorml('Femur_ZAxis1', 'Tibia_YZPlane1')
    Tibia_ZAxis = self.GetNorlm('Tibia_ZAxis1')
    #quxiAngle = self.angle(Femur_ZAxis_Z, Tibia_ZAxis)
    quxiAngle=self.Angle(Femur_ZAxis_Z, Tibia_ZAxis)
        
    Tibia_XAxis = self.GetNorlm('Tibia_XAxis1')
    Tibia_YAxis = self.GetNorlm('Tibia_YAxis1')
    Femur_ZAxis = self.GetNorlm('Femur_ZAxis1')
    ifzf1=np.dot(Tibia_YAxis,Femur_ZAxis)
    print("ifzf1",ifzf1)
    if (ifzf1<0):
      quxiAngle=-quxiAngle
    Femur_XAxis_Z = self.caculateTouYingNorml('Femur_ZAxis1', 'Tibia_YZPlane1')
    waifanAngle=float(self.angle(Femur_XAxis_Z, Femur_ZAxis))
    if(np.dot(Tibia_XAxis,Femur_ZAxis)>0):
      waifanAngle=-waifanAngle

    return quxiAngle,waifanAngle

  def updataJieGuJianxi(self,closet_outside,closet_inside,trans,TibiaJGM):
    a=[closet_outside[0],closet_outside[1],closet_outside[2],1]
    WaiCePoint = np.dot(trans,a)[0:3]
    WaiCePoint1 = self.TouYing(TibiaJGM,WaiCePoint)
    WaiCeLine = slicer.util.getNode('OutSide')
    WaiCeLine.SetNthControlPointPosition(0,WaiCePoint)
    WaiCeLine.SetNthControlPointPosition(1,WaiCePoint1)
    b = [closet_inside[0],closet_inside[1],closet_inside[2],1]
    NeiCePoint = np.dot(trans,b)[0:3]
    NeiCePoint1 = self.TouYing(TibiaJGM,NeiCePoint)
    NeiCeLine = slicer.util.getNode('InSide')
    NeiCeLine.SetNthControlPointPosition(0,NeiCePoint)
    NeiCeLine.SetNthControlPointPosition(1,NeiCePoint1)

  #计算两点在一平面的投影角度
  def caculateTouYingNorml(self, NName, PlaneName):
    PlaneNode = self.GetTransPoint(PlaneName)
    ras1 = [0, 0, 0]
    ras2 = [0, 0, 0]
    slicer.util.getNode(NName).GetNthControlPointPositionWorld(0, ras1)
    slicer.util.getNode(NName).GetNthControlPointPositionWorld(1, ras2)
    n = np.array(self.TouYing(PlaneNode, ras2)) - np.array(self.TouYing(PlaneNode, ras1))
    return n

  # 计算两点点列世界坐标系构成的向量
  def GetNorlm(self, NodeName):
    ras1 = [0, 0, 0]
    ras2 = [0, 0, 0]
    slicer.util.getNode(NodeName).GetNthControlPointPositionWorld(0, ras1)
    slicer.util.getNode(NodeName).GetNthControlPointPositionWorld(1, ras2)
    n1 = np.array([[ras1[0], ras1[1], ras1[2]]])
    n2 = np.array([[ras2[0], ras2[1], ras2[2]]])
    n = n2 - n1
    return n[0]

  # #正常三维视窗状态设置
  # def ThreeDState(self):
  #   #初始化每个三维视窗名字
  #   if self.interactorNum == 0:
  #       self.view1 = slicer.app.layoutManager().threeDWidget('View1').threeDView()
  #       self.view2 = slicer.app.layoutManager().threeDWidget('View2').threeDView()
  #       self.view3 = slicer.app.layoutManager().threeDWidget('View3').threeDView()
  #       self.interactorStyle1 = self.view1.interactorStyle()
  #       self.interactor1 = self.interactorStyle1.GetInteractor()
  #       self.interactorStyle2 = self.view2.interactorStyle()
  #       self.interactor2 = self.interactorStyle2.GetInteractor()
  #       self.interactorStyle3 = self.view3.interactorStyle()
  #       self.interactor3 = self.interactorStyle3.GetInteractor()
  #       self.interactorNum =1
  #   self.interactorStyle1.SetInteractor(self.interactor1)
  #   self.interactorStyle2.SetInteractor(self.interactor2)
  #   self.interactorStyle3.SetInteractor(self.interactor3)

  # 隐藏节点
  def HideNode(self,name):
      try:
          slicer.util.getNode(name).SetDisplayVisibility(False)
      except Exception as e:
          print(e)
  #显示节点
  def ShowNode(self,name):
    try:
      slicer.util.getNode(name).SetDisplayVisibility(True)
    except Exception as e:
      print(e)
  # # 隐藏所有控件
  # def HideAll(self):
  #   self.ui.GuGe.setVisible(False)#骨骼参数
  #   self.ui.ReportWidget.setVisible(False)#手术报告
  #   self.ui.head1.setVisible(False)#骨头调整上面的显示与隐藏        
  #   slicer.modules.popup.widgetRepresentation().hide()#股骨调整
  #   slicer.modules.tibiapopup.widgetRepresentation().hide()#胫骨调整
  #   slicer.modules.viewselect.widgetRepresentation().hide()#股骨视图选择
  #   slicer.modules.tibiaviewselect.widgetRepresentation().hide()#胫骨视图选择
  #   self.ui.OperationPlanWidget.setVisible(False)#存放小部件内容
  #   self.ui.PopupWidget.setVisible(False)#存放模块内容
  #   self.ui.DriveJZWidget.setVisible(False)
  #   self.ui.FemurQGWidget.setVisible(False)
  #   self.ui.Graph.setVisible(False)
  #   self.ui.ForceWidget.setVisible(False)
  #隐藏分割过程中产生的各个部分
  def HidePart(self):
    self.HideNode('股骨切割')
    self.HideNode('Femur')
    self.HideNode('Tibia')
    self.HideNode('胫骨近端')
    self.HideNode('胫骨切割')
    self.HideNode('股骨远端')
    self.HideNode('部件1')
    self.HideNode('部件2')
    self.HideNode('部件3')
    self.HideNode('部件4')
    self.HideNode('部件5')
    self.HideNode('部件6')
    self.HideNode('H点')
    self.HideNode('股骨头球心')
    self.HideNode('A点')
    self.HideNode('内侧后髁')
    self.HideNode('外侧后髁')
    self.HideNode('外侧远端')
    self.HideNode('内侧远端')
    self.HideNode('开髓点')
    self.HideNode('外侧凸点')
    self.HideNode('内侧凹点')
    self.HideNode('外侧皮质高点')
    self.HideNode('外侧高点')
    self.HideNode('内侧高点')
    self.HideNode('胫骨隆凸')
    self.HideNode('胫骨结节')
    self.HideNode('踝穴中心')
    self.HideNode('内侧凸点')

    try:
      self.TibiaJiaTiload.SetDisplayVisibility(False)
    except Exception as e:
      print(e)
    try:
      self.jiatiload.SetDisplayVisibility(False)
    except Exception as e:
      print(e)
    try:
      self.ChenDian.SetDisplayVisibility(False)
    except Exception as e:
      print(e)
  
  #--------------------------------------功能函数-----------------------------------------------
  # 获取transform下的点
  def GetTransPoint(self, node):
    point1, point2, point3 = [0, 0, 0], [0, 0, 0], [0, 0, 0]
    slicer.util.getNode(node).GetNthControlPointPositionWorld(0, point1)
    slicer.util.getNode(node).GetNthControlPointPositionWorld(1, point2)
    slicer.util.getNode(node).GetNthControlPointPositionWorld(2, point3)
    zb = np.array([point1, point2, point3])
    return zb
  # 三个点确定平面方程
  def define_area(self, a):
    point1 = a[0]
    point2 = a[1]
    point3 = a[2]
    AB = np.asmatrix(point2 - point1)
    AC = np.asmatrix(point3 - point1)
    N = np.cross(AB, AC)  # 向量叉乘，求法向量
    # Ax+By+Cz
    Ax = N[0, 0]
    By = N[0, 1]
    Cz = N[0, 2]
    D = -(Ax * point1[0] + By * point1[1] + Cz * point1[2])
    return Ax, By, Cz, D
  # 点到面的距离
  def point2area_distance(self, a, point4):
    Ax, By, Cz, D = self.define_area(a)
    mod_d = Ax * point4[0] + By * point4[1] + Cz * point4[2] + D
    mod_area = np.sqrt(np.sum(np.square([Ax, By, Cz])))
    d = abs(mod_d) / mod_area
    return d
  # 获得投影点（a为三个点确定的平面，point为要获得投影点的点）
  def TouYing(self, a, point):
    Ax, By, Cz, D = self.define_area(a)
    k = (Ax * point[0] + By * point[1] + Cz * point[2] + D) / (np.sum(np.square([Ax, By, Cz])))
    b = [point[0] - k * Ax, point[1] - k * By, point[2] - k * Cz]
    return b
  # 求角度-传递两个向量（求两个向量的夹角）
  def Angle(self, xiangliang1, xiangliang2):
    import math
    cosa = np.dot(xiangliang1, xiangliang2)/math.sqrt(np.dot(xiangliang1,xiangliang1))/math.sqrt(np.dot(xiangliang2, xiangliang2))
    a = math.degrees(math.acos(cosa))
    return a
  #旋转角度变换
  def GetMarix(self,trans,jd,point):
    import math
    jd = math.radians(jd)
    trans_ni=np.linalg.inv(trans)
    Tjxlx=[1,0,0]
    xzjz = [[math.cos(jd) + Tjxlx[0] * Tjxlx[0] * (1 - math.cos(jd)),
                -Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
                Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)), 0],
            [Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
                math.cos(jd) + Tjxlx[1] * Tjxlx[1] * (1 - math.cos(jd)),
                -Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)), 0],
            [-Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)),
                Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)),
                math.cos(jd) + Tjxlx[2] * Tjxlx[2] * (1 - math.cos(jd)), 0],
            [0, 0, 0, 1]]
    
    point=np.array([point[0],point[1],point[2],1])
    point_tmp1=np.dot(trans_ni,point)
    point_tmp2=np.dot(xzjz,point_tmp1)
    point=np.dot(trans,point_tmp2)
    return point[0:3]

  def GetMarix_z(self,jd):
    import math
    jd = math.radians(jd)
    Tjxlx=[0,0,1]
    xzjz = np.array([[math.cos(jd) + Tjxlx[0] * Tjxlx[0] * (1 - math.cos(jd)),
                -Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
                Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)), 0],
            [Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
                math.cos(jd) + Tjxlx[1] * Tjxlx[1] * (1 - math.cos(jd)),
                -Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)), 0],
            [-Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)),
                Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)),
                math.cos(jd) + Tjxlx[2] * Tjxlx[2] * (1 - math.cos(jd)), 0],
            [0, 0, 0, 1]])
    return xzjz

  def GetMarix_x(self,jd):
        jd = math.radians(jd)
        Tjxlx=[1,0,0]
        xzjz = np.array([[math.cos(jd) + Tjxlx[0] * Tjxlx[0] * (1 - math.cos(jd)),
                    -Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
                    Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)), 0],
                [Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
                    math.cos(jd) + Tjxlx[1] * Tjxlx[1] * (1 - math.cos(jd)),
                    -Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)), 0],
                [-Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)),
                    Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)),
                    math.cos(jd) + Tjxlx[2] * Tjxlx[2] * (1 - math.cos(jd)), 0],
                [0, 0, 0, 1]])
        return xzjz
  
  #------------------------------------股骨相机--------------------------------------------------
  #--------------------------------三维视图上的按钮---------------------------------------------
  # 视图1按钮
  def onV1Button(self):
    self.V2Button.click()
    self.V2Button.click()
    if (self.V1Button.toolTip=='<p>锁定</p>'):
      self.interactorStyle1.SetInteractor(None)
      self.V1Button.setToolTip('解锁')

    else:
      self.interactorStyle1.SetInteractor(self.interactor1)
      self.V1Button.setToolTip('锁定')
  # 视图2按钮
  def onV2Button(self):
    cameraNode=self.view1.cameraNode()
    cameraNode2 = self.view2.cameraNode()
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        if (cameraNode.GetName() == 'FC1'):
            if (cameraNode2.GetName() == 'FC2'):
                self.Camera1(self.view2)
                self.Camera2(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.Camera1Tip(self.view2)
                self.Camera2Tip(self.view1)
                self.Camera3Tip(self.view3)
            else:
                self.Camera1(self.view2)
                self.Camera3(self.view1)
                self.DeleteTip(self.view1, self.view3, self.view2)
                self.Camera1Tip(self.view2)
                self.Camera2Tip(self.view3)
                self.Camera3Tip(self.view1)

        elif (cameraNode.GetName() == 'FC2'):
            if (cameraNode2.GetName() == 'FC1'):
                self.Camera1(self.view1)
                self.Camera2(self.view2)
                self.DeleteTip(self.view2, self.view1, self.view3)
                self.Camera1Tip(self.view1)
                self.Camera2Tip(self.view2)
                self.Camera3Tip(self.view3)
            else:
                self.Camera3(self.view1)
                self.Camera2(self.view2)
                self.DeleteTip(self.view3, self.view1, self.view2)
                self.Camera1Tip(self.view3)
                self.Camera2Tip(self.view2)
                self.Camera3Tip(self.view1)
        else:
            if (cameraNode2.GetName() == 'FC2'):
                self.Camera3(self.view2)
                self.Camera2(self.view1)
                self.DeleteTip(self.view3, self.view2, self.view1)
                self.Camera1Tip(self.view3)
                self.Camera2Tip(self.view1)
                self.Camera3Tip(self.view2)
            else:
                self.Camera3(self.view2)
                self.Camera1(self.view1)
                self.DeleteTip(self.view2, self.view3, self.view1)
                self.Camera1Tip(self.view1)
                self.Camera2Tip(self.view3)
                self.Camera3Tip(self.view2)
    else:
        if (cameraNode.GetName() == 'FC1'):
            if (cameraNode2.GetName() == 'FC2'):
                self.Camera1(self.view2)
                self.Camera2(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.Camera1TipRight(self.view2)
                self.Camera2Tip(self.view1)
                self.Camera3TipRight(self.view3)
            else:
                self.Camera1(self.view2)
                self.Camera3(self.view1)
                self.DeleteTip(self.view1, self.view3, self.view2)
                self.Camera1TipRight(self.view2)
                self.Camera2Tip(self.view3)
                self.Camera3TipRight(self.view1)

        elif (cameraNode.GetName() == 'FC2'):
            if (cameraNode2.GetName() == 'FC1'):
                self.Camera1(self.view1)
                self.Camera2(self.view2)
                self.DeleteTip(self.view2, self.view1, self.view3)
                self.Camera1TipRight(self.view1)
                self.Camera2Tip(self.view2)
                self.Camera3TipRight(self.view3)
            else:
                self.Camera3(self.view1)
                self.Camera2(self.view2)
                self.DeleteTip(self.view3, self.view1, self.view2)
                self.Camera1TipRight(self.view3)
                self.Camera2Tip(self.view2)
                self.Camera3TipRight(self.view1)
        else:
            if (cameraNode2.GetName() == 'FC2'):
                self.Camera3(self.view2)
                self.Camera2(self.view1)
                self.DeleteTip(self.view3, self.view2, self.view1)
                self.Camera1TipRight(self.view3)
                self.Camera2Tip(self.view1)
                self.Camera3TipRight(self.view2)
            else:
                self.Camera3(self.view2)
                self.Camera1(self.view1)
                self.DeleteTip(self.view2, self.view3, self.view1)
                self.Camera1TipRight(self.view1)
                self.Camera2Tip(self.view3)
                self.Camera3TipRight(self.view2)
  # 视图3按钮
  def onV3Button(self):
    cameraNode = self.view1.cameraNode()
    cameraNode3 = self.view3.cameraNode()
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        if (cameraNode.GetName() == 'FC1'):
            if (cameraNode3.GetName() == 'FC2'):
                self.Camera1(self.view3)
                self.Camera2(self.view1)
                self.DeleteTip(self.view1, self.view3, self.view2)
                self.Camera1Tip(self.view3)
                self.Camera2Tip(self.view1)
                self.Camera3Tip(self.view2)
            else:
                self.Camera1(self.view3)
                self.Camera3(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.Camera1Tip(self.view3)
                self.Camera2Tip(self.view2)
                self.Camera3Tip(self.view1)
        elif (cameraNode.GetName() == 'FC2'):
            if (cameraNode3.GetName() == 'FC1'):
                self.Camera1(self.view1)
                self.Camera2(self.view3)
                self.DeleteTip(self.view2, self.view3, self.view1)
                self.Camera1Tip(self.view1)
                self.Camera2Tip(self.view3)
                self.Camera3Tip(self.view2)
            else:
                self.Camera3(self.view1)
                self.Camera2(self.view3)
                self.DeleteTip(self.view2, self.view1, self.view3)
                self.Camera1Tip(self.view2)
                self.Camera2Tip(self.view3)
                self.Camera3Tip(self.view1)
        else:
            if (cameraNode3.GetName() == 'FC2'):
                self.Camera3(self.view3)
                self.Camera2(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.Camera1Tip(self.view2)
                self.Camera2Tip(self.view1)
                self.Camera3Tip(self.view3)
            else:
                self.Camera3(self.view3)
                self.Camera1(self.view1)
                self.DeleteTip(self.view3, self.view2, self.view1)
                self.Camera1Tip(self.view1)
                self.Camera2Tip(self.view2)
                self.Camera3Tip(self.view3)
    else:
        if (cameraNode.GetName() == 'FC1'):
            if (cameraNode3.GetName() == 'FC2'):
                self.Camera1(self.view3)
                self.Camera2(self.view1)
                self.DeleteTip(self.view1, self.view3, self.view2)
                self.Camera1TipRight(self.view3)
                self.Camera2Tip(self.view1)
                self.Camera3TipRight(self.view2)
            else:
                self.Camera1(self.view3)
                self.Camera3(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.Camera1TipRight(self.view3)
                self.Camera2Tip(self.view2)
                self.Camera3TipRight(self.view1)
        elif (cameraNode.GetName() == 'FC2'):
            if (cameraNode3.GetName() == 'FC1'):
                self.Camera1(self.view1)
                self.Camera2(self.view3)
                self.DeleteTip(self.view2, self.view3, self.view1)
                self.Camera1TipRight(self.view1)
                self.Camera2Tip(self.view3)
                self.Camera3TipRight(self.view2)
            else:
                self.Camera3(self.view1)
                self.Camera2(self.view3)
                self.DeleteTip(self.view2, self.view1, self.view3)
                self.Camera1TipRight(self.view2)
                self.Camera2Tip(self.view3)
                self.Camera3TipRight(self.view1)
        else:
            if (cameraNode3.GetName() == 'FC2'):
                self.Camera3(self.view3)
                self.Camera2(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.Camera1TipRight(self.view2)
                self.Camera2Tip(self.view1)
                self.Camera3TipRight(self.view3)
            else:
                self.Camera3(self.view3)
                self.Camera1(self.view1)
                self.DeleteTip(self.view3, self.view2, self.view1)
                self.Camera1TipRight(self.view1)
                self.Camera2Tip(self.view2)
                self.Camera3TipRight(self.view3)

  #-------------------------------------三维视图上相机的位置----------------------------------------
  #股骨相机1
  def Camera1(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([0, -500, 0, 1])
    Ftrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('DianjiToTracker1')
    Ftrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ftrans1=np.dot(Ftrans_dj,Ftrans1)
    Ftrans3 = np.dot(Ftrans1, self.Ftrans2)
    position1 = np.dot(Ftrans3, positiontmp)
    viewUpDirection = (float(Ftrans3[0][2]), float(Ftrans3[1][2]), float(Ftrans3[2][2]))
    focalPoint1 = [Ftrans3[0][3], Ftrans3[1][3], Ftrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint1)
    cameraNode.SetPosition(position1[0], position1[1], position1[2])
    cameraNode.SetViewUp(viewUpDirection)
    cameraNode.SetName('FC1')

  #股骨相机2
  def Camera2(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([-500, 0, 0, 1])
    Ftrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('DianjiToTracker1')
    Ftrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ftrans1 = np.dot(Ftrans_dj, Ftrans1)
    Ftrans3 = np.dot(Ftrans1, self.Ftrans2)
    position2 = np.dot(Ftrans3, positiontmp)
    viewUpDirection = (float(Ftrans3[0][2]), float(Ftrans3[1][2]), float(Ftrans3[2][2]))
    focalPoint2 = [Ftrans3[0][3], Ftrans3[1][3], Ftrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint2)
    cameraNode.SetPosition(position2[0], position2[1], position2[2])
    cameraNode.SetViewUp(viewUpDirection)
    cameraNode.SetName('FC2')

  #股骨相机3
  def Camera3(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([0, 0, -500, 1])
    Ftrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('DianjiToTracker1')
    Ftrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ftrans1=np.dot(Ftrans_dj,Ftrans1)
    Ftrans3 = np.dot(Ftrans1, self.Ftrans2)
    position3 = np.dot(Ftrans3, positiontmp)
    viewUpDirection = (-float(Ftrans3[0][1]), -float(Ftrans3[1][1]), -float(Ftrans3[2][1]))
    focalPoint3 = [Ftrans3[0][3], Ftrans3[1][3], Ftrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint3)
    cameraNode.SetPosition(position3[0], position3[1], position3[2])
    cameraNode.SetViewUp(viewUpDirection)
    cameraNode.SetName('FC3')
  #-----------------------------------三维视图上的注释（根据左右腿分内外两侧）--------------------------------
  #相机1注释
  def Camera1Tip(self, view):
      V11 = qt.QLabel(view)
      V12 = qt.QLabel(view)
      V13 = qt.QLabel(view)
      self.V14 = qt.QLabel(view)
      V15 = qt.QLabel(view)
      self.V16 = qt.QLabel(view)
      V17 = qt.QLabel(view)
      V18 = qt.QLabel(view)
      V19 = qt.QLabel(view)
      self.V1A = qt.QLabel(view)
      V1B = qt.QLabel(view)
      self.V1C = qt.QLabel(view)

      V11.setObjectName('1')
      V12.setObjectName('2')
      V13.setObjectName('3')
      self.V14.setObjectName('4')
      V15.setObjectName('5')
      self.V16.setObjectName('6')
      V17.setObjectName('7')
      V18.setObjectName('8')
      V19.setObjectName('9')
      self.V1A.setObjectName('10')
      V1B.setObjectName('11')
      self.V1C.setObjectName('12')

      V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
      V11.setText(" 外翻/内翻 ")
      V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V11.show()
      try:
          V12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
          V12.setText(' '+str(round(self.WaiFanJiao,1))+'°')
          V12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
          V12.show()
      except Exception as e:
          print(e)

      V13.setGeometry(0, view.contentsRect().height() - 125, 100, 25)
      V13.setText(" 内侧远端截骨 ")
      V13.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V13.show()
      self.V14.setGeometry(0, view.contentsRect().height() - 100, 100, 25)
      try:
          self.V14.setText(' '+ str(round(slicer.modules.PopupWidget.FemurNeiCeYuanDuan, 1))+ 'mm')
      except Exception as e:
          print(e)
      self.V14.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V14.show()
      V15.setGeometry(0, view.contentsRect().height() - 75, 100, 25)
      V15.setText(" 内侧伸直间隙 ")
      V15.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V15.show()
      self.V16.setGeometry(0, view.contentsRect().height() - 50, 100, 25)
      self.V16.setText("")
      self.V16.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V16.show()
      V17.setGeometry(5, 0.5 * view.contentsRect().height(), 100, 40)
      V17.setText("内 ")
      V17.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V17.show()
      V18.setGeometry(view.contentsRect().width() - 50, 0.5 * view.contentsRect().height(), 100, 40)
      V18.setText(" 外 ")
      V18.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V18.show()
      V19.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 125, 100, 25)
      V19.setText(" 外侧远端截骨 ")
      V19.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V19.show()
      self.V1A.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 100, 100, 25)
      try:
          self.V1A.setText(' ' + str(round(slicer.modules.PopupWidget.FemurWaiCeYuanDuan, 1)) + 'mm')
      except Exception as e:
          print(e)
      self.V1A.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V1A.show()
      V1B.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 75, 100, 25)
      V1B.setText(" 外侧伸直间隙 ")
      V1B.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V1B.show()
      self.V1C.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 50, 100, 25)
      self.V1C.setText("")
      self.V1C.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V1C.show()

  def Camera1TipRight(self, view):
      V11 = qt.QLabel(view)
      V12 = qt.QLabel(view)
      V13 = qt.QLabel(view)
      self.V14 = qt.QLabel(view)
      V15 = qt.QLabel(view)
      self.V16 = qt.QLabel(view)
      V17 = qt.QLabel(view)
      V18 = qt.QLabel(view)
      V19 = qt.QLabel(view)
      self.V1A = qt.QLabel(view)
      V1B = qt.QLabel(view)
      self.V1C = qt.QLabel(view)

      V11.setObjectName('1')
      V12.setObjectName('2')
      V13.setObjectName('3')
      self.V14.setObjectName('4')
      V15.setObjectName('5')
      self.V16.setObjectName('6')
      V17.setObjectName('7')
      V18.setObjectName('8')
      V19.setObjectName('9')
      self.V1A.setObjectName('10')
      V1B.setObjectName('11')
      self.V1C.setObjectName('12')

      V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
      V11.setText(" 外翻/内翻 ")
      V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V11.show()
      try:
          V12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
          V12.setText(' '+str(round(self.WaiFanJiao,1))+'°')
          V12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
          V12.show()
      except Exception as e:
          print(e)

      V13.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 125, 100, 25)
      V13.setText(" 内侧远端截骨 ")
      V13.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V13.show()
      self.V14.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 100, 100, 25)
      try:
          self.V14.setText(' '+ str(round(slicer.modules.PopupWidget.FemurNeiCeYuanDuan, 1))+ 'mm')
      except Exception as e:
          print(e)
      self.V14.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V14.show()
      V15.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 75, 100, 25)
      V15.setText(" 内侧伸直间隙 ")
      V15.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V15.show()
      self.V16.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 50, 100, 25)
      self.V16.setText("")
      self.V16.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V16.show()
      V17.setGeometry(view.contentsRect().width() - 50, 0.5 * view.contentsRect().height(), 100, 40)
      V17.setText(" 内 ")
      V17.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V17.show()
      V18.setGeometry( 5, 0.5 * view.contentsRect().height(), 100, 40)
      V18.setText("外 ")
      V18.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V18.show()
      V19.setGeometry(0, view.contentsRect().height() - 125, 100, 25)
      V19.setText(" 外侧远端截骨 ")
      V19.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V19.show()
      self.V1A.setGeometry( 0, view.contentsRect().height() - 100, 100, 25)
      try:
          self.V1A.setText(' ' + str(round(slicer.modules.PopupWidget.FemurWaiCeYuanDuan, 1)) + 'mm')
      except Exception as e:
          print(e)
      self.V1A.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V1A.show()
      V1B.setGeometry( 0, view.contentsRect().height() - 75, 100, 25)
      V1B.setText(" 外侧伸直间隙 ")
      V1B.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V1B.show()
      self.V1C.setGeometry( 0, view.contentsRect().height() - 50, 100, 25)
      self.V1C.setText("")
      self.V1C.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V1C.show()

  #相机2注释
  def Camera2Tip(self, view):
      V11 = qt.QLabel(view)
      self.V12 = qt.QLabel(view)
      V13 = qt.QLabel(view)
      V14 = qt.QLabel(view)

      V11.setObjectName('13')
      self.V12.setObjectName('14')
      V13.setObjectName('15')
      V14.setObjectName('16')

      V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
      V11.setText(" 前倾/后倾 ")
      V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V11.show()
      
      try:
          self.V12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
          self.V12.setText(' '+str(round(slicer.modules.PopupWidget.HouQingJiao,1))+'°')
          self.V12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
          self.V12.show()
          
      except Exception as e:
          print(e)
      V13.setGeometry(5, 0.5*view.contentsRect().height(), 100, 40)
      V13.setText("前 ")
      V13.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V13.show()
      V14.setGeometry(view.contentsRect().width() - 50, 0.5*view.contentsRect().height(), 100, 40)
      V14.setText(" 后 ")
      V14.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V14.show()

  def Camera2TipRight(self, view):
      V11 = qt.QLabel(view)
      self.V12 = qt.QLabel(view)
      V13 = qt.QLabel(view)
      V14 = qt.QLabel(view)

      V11.setObjectName('13')
      self.V12.setObjectName('14')
      V13.setObjectName('15')
      V14.setObjectName('16')

      V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
      V11.setText(" 前倾/后倾 ")
      V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V11.show()

      try:
          self.V12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
          self.V12.setText(' ' + str(round(slicer.modules.PopupWidget.HouQingJiao, 1)) + '°')
          self.V12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
          self.V12.show()

      except Exception as e:
          print(e)
      V13.setGeometry(5, 0.5*view.contentsRect().height(), 100, 40)
      V13.setText("前 ")
      V13.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V13.show()
      V14.setGeometry(view.contentsRect().width() - 50, 0.5*view.contentsRect().height(), 100, 40)
      V14.setText(" 后 ")
      V14.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V14.show()

  #相机3注释
  def Camera3Tip(self, view):
      V21 = qt.QLabel(view)
      self.V22 = qt.QLabel(view)
      V23 = qt.QLabel(view)
      self.V24 = qt.QLabel(view)
      V25 = qt.QLabel(view)
      self.V26 = qt.QLabel(view)
      V27 = qt.QLabel(view)
      V28 = qt.QLabel(view)
      V29 = qt.QLabel(view)
      self.V2A = qt.QLabel(view)
      V2B = qt.QLabel(view)
      self.V2C = qt.QLabel(view)

      V21.setObjectName('1')
      self.V22.setObjectName('2')
      V23.setObjectName('3')
      self.V24.setObjectName('4')
      V25.setObjectName('5')
      self.V26.setObjectName('6')
      V27.setObjectName('7')
      V28.setObjectName('8')
      V29.setObjectName('9')
      self.V2A.setObjectName('10')
      V2B.setObjectName('11')
      self.V2C.setObjectName('12')

      V21.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
      V21.setText(" 外旋/内旋 ")
      V21.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V21.show()
      self.V22.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
      try:

          self.V22.setText(' '+str(round(slicer.modules.PopupWidget.WaiXuanJiao, 1))+'°')

      except Exception as e:
          print(e)
      self.V22.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V22.show()
      V23.setGeometry(0, view.contentsRect().height() - 125, 100, 25)
      V23.setText(" 内侧后髁截骨 ")
      V23.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V23.show()
      self.V24.setGeometry(0, view.contentsRect().height() - 100, 100, 25)
      try:
          self.V24.setText(
              ' ' + str(round(slicer.modules.PopupWidget.FemurNeiCeHouKe, 1)) + 'mm')
      except Exception as e:
          print(e)

      self.V24.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V24.show()
      V25.setGeometry(0, view.contentsRect().height() - 75, 100, 25)
      V25.setText(" 内侧屈膝截骨 ")
      V25.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V25.show()
      self.V26.setGeometry(0, view.contentsRect().height() - 50, 100, 25)
      self.V26.setText("")
      self.V26.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V26.show()
      V27.setGeometry(5, 0.5*view.contentsRect().height(), 100, 40)
      V27.setText("内 ")
      V27.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V27.show()
      V28.setGeometry(view.contentsRect().width() - 50, 0.5*view.contentsRect().height(), 100, 40)
      V28.setText(" 外 ")
      V28.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
      V28.show()
      V29.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 125, 100, 25)
      V29.setText(" 外侧后髁截骨 ")
      V29.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V29.show()
      self.V2A.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 100, 100, 25)
      try:
          self.V2A.setText( ' ' + str(round(slicer.modules.PopupWidget.FemurWaiCeHouKe, 1)) + 'mm')
      except Exception as e:
          print(e)
      self.V2A.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V2A.show()
      V2B.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 75, 100, 25)
      V2B.setText(" 外侧屈膝截骨 ")
      V2B.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      V2B.show()
      self.V2C.setGeometry(view.contentsRect().width() - 100,view.contentsRect().height() - 50, 100, 25)
      self.V2C.setText("")
      self.V2C.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
      self.V2C.show()

  def Camera3TipRight(self, view):
    V21 = qt.QLabel(view)
    self.V22 = qt.QLabel(view)
    V23 = qt.QLabel(view)
    self.V24 = qt.QLabel(view)
    V25 = qt.QLabel(view)
    self.V26 = qt.QLabel(view)
    V27 = qt.QLabel(view)
    V28 = qt.QLabel(view)
    V29 = qt.QLabel(view)
    self.V2A = qt.QLabel(view)
    V2B = qt.QLabel(view)
    self.V2C = qt.QLabel(view)

    V21.setObjectName('1')
    self.V22.setObjectName('2')
    V23.setObjectName('3')
    self.V24.setObjectName('4')
    V25.setObjectName('5')
    self.V26.setObjectName('6')
    V27.setObjectName('7')
    V28.setObjectName('8')
    V29.setObjectName('9')
    self.V2A.setObjectName('10')
    V2B.setObjectName('11')
    self.V2C.setObjectName('12')

    V21.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
    V21.setText(" 外旋/内旋 ")
    V21.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V21.show()
    self.V22.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
    try:

        self.V22.setText(' '+str(round(slicer.modules.PopupWidget.WaiXuanJiao, 1))+'°')

    except Exception as e:
        print(e)
    self.V22.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V22.show()
    V23.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 125, 100, 25)
    V23.setText(" 内侧后髁截骨 ")
    V23.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V23.show()
    self.V24.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 100, 100, 25)
    try:
        self.V24.setText(
            ' ' + str(round(slicer.modules.PopupWidget.FemurNeiCeHouKe, 1)) + 'mm')
    except Exception as e:
        print(e)

    self.V24.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V24.show()
    V25.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 75, 100, 25)
    V25.setText(" 内侧屈曲截骨 ")
    V25.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V25.show()
    self.V26.setGeometry(view.contentsRect().width() - 100,view.contentsRect().height() - 50, 100, 25)
    self.V26.setText("")
    self.V26.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V26.show()
    V27.setGeometry(view.contentsRect().width() - 100, 0.5*view.contentsRect().height(), 100, 40)
    V27.setText(" 内 ")
    V27.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V27.show()
    V28.setGeometry( 5, 0.5*view.contentsRect().height(), 100, 40)
    V28.setText("外 ")
    V28.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V28.show()
    V29.setGeometry( 0, view.contentsRect().height() - 125, 100, 25)
    V29.setText(" 外侧后髁截骨 ")
    V29.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V29.show()
    self.V2A.setGeometry( 0, view.contentsRect().height() - 100, 100, 25)
    try:
        self.V2A.setText( ' ' + str(round(slicer.modules.PopupWidget.FemurWaiCeHouKe, 1)) + 'mm')
    except Exception as e:
        print(e)
    self.V2A.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V2A.show()
    V2B.setGeometry( 0, view.contentsRect().height() - 75, 100, 25)
    V2B.setText(" 外侧屈曲截骨 ")
    V2B.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V2B.show()
    self.V2C.setGeometry( 0, view.contentsRect().height() - 50, 100, 25)
    self.V2C.setText("")
    self.V2C.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V2C.show()
  #------------------------------胫骨相机------------------------------------------------------
  # 胫骨相机1
  def TCamera1(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([0, -500, 0, 1])
    Ttrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('TibiaToTracker')
    Ttrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ttrans1=np.dot(Ttrans_dj,Ttrans1)
    Ttrans3 = np.dot(Ttrans1, self.Ttrans2)
    position1 = np.dot(Ttrans3, positiontmp)
    viewUpDirection = (float(Ttrans3[0][2]), float(Ttrans3[1][2]), float(Ttrans3[2][2]))
    focalPoint1 = [Ttrans3[0][3], Ttrans3[1][3], Ttrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint1)
    cameraNode.SetPosition(position1[0], position1[1], position1[2])
    cameraNode.SetViewUp(viewUpDirection)
    #self.Camera1(view)
    view.cameraNode().SetName('TC1')

  # 胫骨相机2
  def TCamera2(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([-500, 0, 0, 1])
    Ttrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('TibiaToTracker')
    Ttrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ttrans1=np.dot(Ttrans_dj,Ttrans1)
    Ttrans3 = np.dot(Ttrans1, self.Ttrans2)
    position2 = np.dot(Ttrans3, positiontmp)
    viewUpDirection = (float(Ttrans3[0][2]), float(Ttrans3[1][2]), float(Ttrans3[2][2]))
    focalPoint2 = [Ttrans3[0][3], Ttrans3[1][3], Ttrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint2)
    cameraNode.SetPosition(position2[0], position2[1], position2[2])
    cameraNode.SetViewUp(viewUpDirection)
    #self.Camera2(view)
    view.cameraNode().SetName('TC2')

  # 胫骨相机3
  def TCamera3(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([0, 0, 500, 1])
    Ttrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('TibiaToTracker')
    Ttrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ttrans1=np.dot(Ttrans_dj,Ttrans1)
    Ttrans3 = np.dot(Ttrans1, self.Ttrans2)
    position3 = np.dot(Ttrans3, positiontmp)
    viewUpDirection = (float(Ttrans3[0][1]), float(Ttrans3[1][1]), float(Ttrans3[2][1]))
    focalPoint3 = [Ttrans3[0][3], Ttrans3[1][3], Ttrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint3)
    cameraNode.SetPosition(position3[0], position3[1], position3[2])
    cameraNode.SetViewUp(viewUpDirection)
    #self.Camera3(view)
    view.cameraNode().SetName('TC3')
  
  # 胫骨视图1按钮
  def onTV1Button(self):
    self.TV2Button.click()
    self.TV2Button.click()
    if (self.TV1Button.toolTip=='<p>锁定</p>'):
        self.interactorStyle1.SetInteractor(None)
        self.TV1Button.setToolTip('解锁')

    else:
        self.interactorStyle1.SetInteractor(self.interactor1)
        self.TV1Button.setToolTip('锁定')

  # 胫骨视图2按钮
  def onTV2Button(self):
    cameraNode=self.view1.cameraNode()
    cameraNode2 = self.view2.cameraNode()
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      if (cameraNode.GetName() == 'TC1'):
        if (cameraNode2.GetName() == 'TC2'):
          self.TCamera1(self.view2)
          self.TCamera2(self.view1)
          self.DeleteTip(self.view1, self.view2, self.view3)
          self.TCamera1Tip(self.view2)
          self.TCamera2Tip(self.view1)
          self.TCamera3Tip(self.view3)
        else:
          self.TCamera3(self.view1)
          self.TCamera1(self.view2)
          self.DeleteTip(self.view1, self.view3, self.view2)
          self.TCamera1Tip(self.view2)
          self.TCamera2Tip(self.view3)
          self.TCamera3Tip(self.view1)
      elif (cameraNode.GetName() == 'TC2'):
        if (cameraNode2.GetName() == 'TC1'):
          self.TCamera1(self.view1)
          self.TCamera2(self.view2)
          self.DeleteTip(self.view2, self.view1, self.view3)
          self.TCamera1Tip(self.view1)
          self.TCamera2Tip(self.view2)
          self.TCamera3Tip(self.view3)
        else:
          self.TCamera3(self.view1)
          self.TCamera2(self.view2)
          self.DeleteTip(self.view3, self.view1, self.view2)
          self.TCamera1Tip(self.view3)
          self.TCamera2Tip(self.view2)
          self.TCamera3Tip(self.view1)
      else:
        if (cameraNode2.GetName() == 'TC2'):
          self.TCamera3(self.view2)
          self.TCamera2(self.view1)
          self.DeleteTip(self.view3, self.view2, self.view1)
          self.TCamera1Tip(self.view3)
          self.TCamera2Tip(self.view1)
          self.TCamera3Tip(self.view2)
        else:
          self.TCamera3(self.view2)
          self.TCamera1(self.view1)
          self.DeleteTip(self.view2, self.view3, self.view1)
          self.TCamera1Tip(self.view1)
          self.TCamera2Tip(self.view3)
          self.TCamera3Tip(self.view2)
    else:
      if (cameraNode.GetName() == 'TC1'):
        if (cameraNode2.GetName() == 'TC2'):
            self.TCamera1(self.view2)
            self.TCamera2(self.view1)
            self.DeleteTip(self.view1, self.view2, self.view3)
            self.TCamera1TipRight(self.view2)
            self.TCamera2Tip(self.view1)
            self.TCamera3TipRight(self.view3)
        else:
            self.TCamera3(self.view1)
            self.TCamera1(self.view2)
            self.DeleteTip(self.view1, self.view3, self.view2)
            self.TCamera1TipRight(self.view2)
            self.TCamera2Tip(self.view3)
            self.TCamera3TipRight(self.view1)
      elif (cameraNode.GetName() == 'TC2'):
        if (cameraNode2.GetName() == 'TC1'):
          self.TCamera1(self.view1)
          self.TCamera2(self.view2)
          self.DeleteTip(self.view2, self.view1, self.view3)
          self.TCamera1TipRight(self.view1)
          self.TCamera2Tip(self.view2)
          self.TCamera3TipRight(self.view3)
        else:
          self.TCamera3(self.view1)
          self.TCamera2(self.view2)
          self.DeleteTip(self.view3, self.view1, self.view2)
          self.TCamera1TipRight(self.view3)
          self.TCamera2Tip(self.view2)
          self.TCamera3TipRight(self.view1)
      else:
        if (cameraNode2.GetName() == 'TC2'):
          self.TCamera3(self.view2)
          self.TCamera2(self.view1)
          self.DeleteTip(self.view3, self.view2, self.view1)
          self.TCamera1TipRight(self.view3)
          self.TCamera2Tip(self.view1)
          self.TCamera3TipRight(self.view2)
        else:
          self.TCamera3(self.view2)
          self.TCamera1(self.view1)
          self.DeleteTip(self.view2, self.view3, self.view1)
          self.TCamera1TipRight(self.view1)
          self.TCamera2Tip(self.view3)
          self.TCamera3TipRight(self.view2)

  # 胫骨视图3按钮
  def onTV3Button(self):
    viewNode1 = slicer.mrmlScene.GetSingletonNode("1", "vtkMRMLViewNode")
    cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode1)
    viewNode3 = slicer.mrmlScene.GetSingletonNode("3", "vtkMRMLViewNode")
    cameraNode3 = slicer.modules.cameras.logic().GetViewActiveCameraNode(viewNode3)
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        if (cameraNode.GetName() == 'TC1'):
            if (cameraNode3.GetName() == 'TC2'):
                self.TCamera1(self.view3)
                self.TCamera2(self.view1)
                self.DeleteTip(self.view1, self.view3, self.view2)
                self.TCamera1Tip(self.view3)
                self.TCamera2Tip(self.view1)
                self.TCamera3Tip(self.view2)
            else:
                self.TCamera3(self.view1)
                self.TCamera1(self.view3)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.TCamera1Tip(self.view3)
                self.TCamera2Tip(self.view2)
                self.TCamera3Tip(self.view1)

        elif (cameraNode.GetName() == 'TC2'):
            if (cameraNode3.GetName() == 'TC1'):
                self.TCamera1(self.view1)
                self.TCamera2(self.view3)
                self.DeleteTip(self.view2, self.view3, self.view1)
                self.TCamera1Tip(self.view1)
                self.TCamera2Tip(self.view3)
                self.TCamera3Tip(self.view2)
            else:
                self.TCamera3(self.view1)
                self.TCamera2(self.view3)
                self.DeleteTip(self.view2, self.view1, self.view3)
                self.TCamera1Tip(self.view2)
                self.TCamera2Tip(self.view3)
                self.TCamera3Tip(self.view1)
        else:
            if (cameraNode3.GetName() == 'TC2'):
                self.TCamera3(self.view3)
                self.TCamera2(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.TCamera1Tip(self.view2)
                self.TCamera2Tip(self.view1)
                self.TCamera3Tip(self.view3)
            else:
                self.TCamera3(self.view3)
                self.TCamera1(self.view1)
                self.DeleteTip(self.view3, self.view2, self.view1)
                self.TCamera1Tip(self.view1)
                self.TCamera2Tip(self.view2)
                self.TCamera3Tip(self.view3)
    else:
        if (cameraNode.GetName() == 'TC1'):
            if (cameraNode3.GetName() == 'TC2'):
                self.TCamera1(self.view3)
                self.TCamera2(self.view1)
                self.DeleteTip(self.view1, self.view3, self.view2)
                self.TCamera1TipRight(self.view3)
                self.TCamera2Tip(self.view1)
                self.TCamera3TipRight(self.view2)
            else:
                self.TCamera3(self.view1)
                self.TCamera1(self.view3)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.TCamera1TipRight(self.view3)
                self.TCamera2Tip(self.view2)
                self.TCamera3TipRight(self.view1)

        elif (cameraNode.GetName() == 'TC2'):
            if (cameraNode3.GetName() == 'TC1'):
                self.TCamera1(self.view1)
                self.TCamera2(self.view3)
                self.DeleteTip(self.view2, self.view3, self.view1)
                self.TCamera1TipRight(self.view1)
                self.TCamera2Tip(self.view3)
                self.TCamera3TipRight(self.view2)
            else:
                self.TCamera3(self.view1)
                self.TCamera2(self.view3)
                self.DeleteTip(self.view2, self.view1, self.view3)
                self.TCamera1TipRight(self.view2)
                self.TCamera2Tip(self.view3)
                self.TCamera3TipRight(self.view1)
        else:
            if (cameraNode3.GetName() == 'TC2'):
                self.TCamera3(self.view3)
                self.TCamera2(self.view1)
                self.DeleteTip(self.view1, self.view2, self.view3)
                self.TCamera1TipRight(self.view2)
                self.TCamera2Tip(self.view1)
                self.TCamera3TipRight(self.view3)
            else:
                self.TCamera3(self.view3)
                self.TCamera1(self.view1)
                self.DeleteTip(self.view3, self.view2, self.view1)
                self.TCamera1TipRight(self.view1)
                self.TCamera2Tip(self.view2)
                self.TCamera3TipRight(self.view3)
  
  #胫骨相机1注释
  def TCamera1Tip(self, view):
    V11 = qt.QLabel(view)
    V12 = qt.QLabel(view)
    V13 = qt.QLabel(view)
    self.V14 = qt.QLabel(view)
    V15 = qt.QLabel(view)
    self.V16 = qt.QLabel(view)
    V17 = qt.QLabel(view)
    V18 = qt.QLabel(view)
    V19 = qt.QLabel(view)
    self.V1A = qt.QLabel(view)
    V1B = qt.QLabel(view)
    self.V1C = qt.QLabel(view)
    V1D = qt.QLabel(view)
    self.V1E = qt.QLabel(view)
    V1F = qt.QLabel(view)
    self.V1G = qt.QLabel(view)

    V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
    V11.setText(" 外翻/内翻 ")
    V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V11.show()
    try:
        V12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
        V12.setText(' 0.0°')
        V12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
        V12.show()
    except Exception as e:
        print(e)

    V1D.setGeometry(0, view.contentsRect().height() - 175, 100, 25)
    V1D.setText(" 内侧截骨 ")
    V1D.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V1D.show()

    self.V1E.setGeometry(0, view.contentsRect().height() - 150, 100, 25)
    try:
        self.V1E.setText(" "+str(round(slicer.modules.TibiaPopupWidget.TibiaNeiCeJieGu,1))+"mm")
    except Exception as e:
        print(e)
    self.V1E.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1E.show()


    V13.setGeometry(0, view.contentsRect().height() - 125, 100, 25)
    V13.setText(" 内侧伸直间隙 ")
    V13.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V13.show()
    self.V14.setGeometry(0, view.contentsRect().height() - 100, 100, 25)
    self.V14.setText("")
    self.V14.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V14.show()
    V15.setGeometry(0, view.contentsRect().height() - 75, 100, 25)
    V15.setText(" 内侧屈膝间隙 ")
    V15.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V15.show()
    self.V16.setGeometry(0, view.contentsRect().height() - 50, 100, 25)
    self.V16.setText("")
    self.V16.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V16.show()
    V17.setGeometry(5, 0.5 * view.contentsRect().height(), 100, 40)
    V17.setText("内 ")
    V17.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V17.show()
    V18.setGeometry(view.contentsRect().width() - 50, 0.5 * view.contentsRect().height(), 100, 40)
    V18.setText(" 外 ")
    V18.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V18.show()

    V1F.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 175, 100, 25)
    V1F.setText(" 外侧截骨 ")
    V1F.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V1F.show()
    self.V1G.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 150, 100, 25)
    try:
        self.V1G.setText(" "+str(round(slicer.modules.TibiaPopupWidget.TibiaWaiCeJieGu,1))+"mm")
    except Exception as e:
        print(e)
    self.V1G.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1G.show()

    V19.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 125, 100, 25)
    V19.setText(" 外侧伸直间隙 ")
    V19.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V19.show()
    self.V1A.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 100, 100, 25)
    self.V1A.setText("")
    self.V1A.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1A.show()
    V1B.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 75, 100, 25)
    V1B.setText(" 外侧屈膝间隙 ")
    V1B.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V1B.show()
    self.V1C.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 50, 100, 25)
    self.V1C.setText("")
    self.V1C.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1C.show()
  
  #右侧胫骨相机1注释
  def TCamera1TipRight(self, view):
    V11 = qt.QLabel(view)
    V12 = qt.QLabel(view)
    V13 = qt.QLabel(view)
    self.V14 = qt.QLabel(view)
    V15 = qt.QLabel(view)
    self.V16 = qt.QLabel(view)
    V17 = qt.QLabel(view)
    V18 = qt.QLabel(view)
    V19 = qt.QLabel(view)
    self.V1A = qt.QLabel(view)
    V1B = qt.QLabel(view)
    self.V1C = qt.QLabel(view)
    V1D = qt.QLabel(view)
    self.V1E = qt.QLabel(view)
    V1F = qt.QLabel(view)
    self.V1G = qt.QLabel(view)

    V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
    V11.setText(" 外翻/内翻 ")
    V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V11.show()
    try:
        V12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
        V12.setText(' 0.0°')
        V12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
        V12.show()
    except Exception as e:
        print(e)

    V1D.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 175, 100, 25)
    V1D.setText(" 内侧截骨 ")
    V1D.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V1D.show()

    self.V1E.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 150, 100, 25)
    try:
        self.V1E.setText(" "+str(round(slicer.modules.TibiaPopupWidget.TibiaNeiCeJieGu,1))+"mm")
    except Exception as e:
        print(e)
    self.V1E.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1E.show()


    V13.setGeometry(view.contentsRect().width() - 100, view.contentsRect().height() - 125, 100, 25)
    V13.setText(" 内侧伸直间隙 ")
    V13.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V13.show()
    self.V14.setGeometry( view.contentsRect().width() - 100, view.contentsRect().height() - 100, 100, 25)
    self.V14.setText("")
    self.V14.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V14.show()
    V15.setGeometry( view.contentsRect().width() - 100, view.contentsRect().height() - 75, 100, 25)
    V15.setText(" 内侧屈膝间隙 ")
    V15.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V15.show()
    self.V16.setGeometry( view.contentsRect().width() - 100, view.contentsRect().height() - 50, 100, 25)
    self.V16.setText("")
    self.V16.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V16.show()
    V17.setGeometry(view.contentsRect().width() - 50, 0.5 * view.contentsRect().height(), 100, 40)
    V17.setText(" 内 ")
    V17.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V17.show()
    V18.setGeometry( 5, 0.5 * view.contentsRect().height(), 100, 40)
    V18.setText("外 ")
    V18.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V18.show()

    V1F.setGeometry( 0, view.contentsRect().height() - 175, 100, 25)
    V1F.setText(" 外侧截骨 ")
    V1F.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V1F.show()
    self.V1G.setGeometry( 0, view.contentsRect().height() - 150, 100, 25)
    try:
        self.V1G.setText(" "+str(round(slicer.modules.TibiaPopupWidget.TibiaWaiCeJieGu,1))+"mm")
    except Exception as e:
        print(e)
    self.V1G.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1G.show()

    V19.setGeometry( 0, view.contentsRect().height() - 125, 100, 25)
    V19.setText(" 外侧伸直间隙 ")
    V19.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V19.show()
    self.V1A.setGeometry(0, view.contentsRect().height() - 100, 100, 25)
    self.V1A.setText("")
    self.V1A.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1A.show()
    V1B.setGeometry(0, view.contentsRect().height() - 75, 100, 25)
    V1B.setText(" 外侧屈膝间隙 ")
    V1B.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V1B.show()
    self.V1C.setGeometry(0, view.contentsRect().height() - 50, 100, 25)
    self.V1C.setText("")
    self.V1C.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.V1C.show()

  # 胫骨相机2注释
  def TCamera2Tip(self, view):
    V11 = qt.QLabel(view)
    self.T12 = qt.QLabel(view)
    V13 = qt.QLabel(view)
    V14 = qt.QLabel(view)
    V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
    V11.setText(" 前倾/后倾 ")
    V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V11.show()
    self.T12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
    try:
        self.T12.setText(' '+str(round(slicer.modules.TibiaPopupWidget.TibiaHouQingJiao, 1))+'°')
    except Exception as e:
        print(e)
    self.T12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.T12.show()
    V13.setGeometry(5, 0.5 * view.contentsRect().height(), 100, 40)
    V13.setText("前 ")
    V13.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V13.show()
    V14.setGeometry(view.contentsRect().width() - 50, 0.5 * view.contentsRect().height(), 100, 40)
    V14.setText(" 后 ")
    V14.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V14.show()

  # 胫骨相机3注释
  def TCamera3Tip(self, view):
    V21 = qt.QLabel(view)
    self.T22 = qt.QLabel(view)
    V23 = qt.QLabel(view)
    V24 = qt.QLabel(view)

    V21.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
    V21.setText(" 外旋/内旋 ")
    V21.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V21.show()
    self.T22.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
    try:
        self.T22.setText(' '+str(round(slicer.modules.TibiaPopupWidget.TibiaWaiXuanJiao, 1))+'°')
    except Exception as e:
        print(e)

    self.T22.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.T22.show()
    V23.setGeometry(5, 0.5 * view.contentsRect().height(), 100, 40)
    V23.setText("内 ")
    V23.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V23.show()
    V24.setGeometry(view.contentsRect().width() - 50, 0.5 * view.contentsRect().height(), 100, 40)
    V24.setText(" 外 ")
    V24.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V24.show()

  def TCamera3TipRight(self, view):
    V21 = qt.QLabel(view)
    self.T22 = qt.QLabel(view)
    V23 = qt.QLabel(view)
    V24 = qt.QLabel(view)

    V21.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
    V21.setText(" 外旋/内旋 ")
    V21.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V21.show()
    self.T22.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
    try:
        self.T22.setText(' '+str(round(slicer.modules.TibiaPopupWidget.TibiaWaiXuanJiao, 1))+'°')
    except Exception as e:
        print(e)

    self.T22.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.T22.show()
    V23.setGeometry(view.contentsRect().width() - 50, 0.5 * view.contentsRect().height(), 100, 40)
    V23.setText(" 内 ")
    V23.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V23.show()
    V24.setGeometry( 5, 0.5 * view.contentsRect().height(), 100, 40)
    V24.setText("外 ")
    V24.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V24.show()

    V21 = qt.QLabel(view)
    self.T22 = qt.QLabel(view)
    V23 = qt.QLabel(view)
    V24 = qt.QLabel(view)

    V21.setGeometry(view.contentsRect().width() - 100, 25, 100, 40)
    V21.setText(" 外旋/内旋 ")
    V21.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    V21.show()
    self.T22.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
    try:
        self.T22.setText(' '+str(round(slicer.modules.TibiaPopupWidget.TibiaWaiXuanJiao, 1))+'°')
    except Exception as e:
        print(e)

    self.T22.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    self.T22.show()
    V23.setGeometry(view.contentsRect().width() - 100, 0.5 * view.contentsRect().height(), 100, 40)
    V23.setText(" 内侧 ")
    V23.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V23.show()
    V24.setGeometry( 5, 0.5 * view.contentsRect().height(), 100, 40)
    V24.setText(" 外侧 ")
    V24.setStyleSheet('QLabel{background-color:transparent;color:#A9A9A9;font:30px;}')
    V24.show()

  # 隐藏三维视图显示的信息及按钮
  def hideInformation(self):
    try:
      self.V1Button.hide()
      self.V2Button.hide()
      self.V3Button.hide()
    except Exception as e:
      print(e)

    try:
      self.TV1Button.hide()
      self.TV2Button.hide()
      self.TV3Button.hide()
    except Exception as e:
      print(e)

    self.DeleteTip(self.view1, self.view2, self.view3)
  #删除Tip
  def DeleteTip(self, view1, view2, view3):
    for i in range(0, len(view1.findChildren(qt.QLabel))):
        view1.findChildren(qt.QLabel)[-1].delete()
    for i in range(0, len(view2.findChildren(qt.QLabel))):
        view2.findChildren(qt.QLabel)[-1].delete()
    for i in range(0, len(view3.findChildren(qt.QLabel))):
        view3.findChildren(qt.QLabel)[-1].delete()
  #三维视图观察者添加
  def AddObserver(self):
    self.view1Observer = slicer.util.getNode('vtkMRMLViewNode1').AddObserver(vtk.vtkWidgetEvent.Resize,self.UpdateTip)
    self.view2Observer = slicer.util.getNode('vtkMRMLViewNode2').AddObserver(vtk.vtkCommand.ModifiedEvent,self.UpdateTip)
    self.view3Observer = slicer.util.getNode('vtkMRMLViewNode3').AddObserver(vtk.vtkCommand.ModifiedEvent,self.UpdateTip)
  #三维视图观察者移除
  def RemoveObserver(self):
    slicer.util.getNode('vtkMRMLViewNode1').RemoveObserver(self.view1Observer)
    slicer.util.getNode('vtkMRMLViewNode2').RemoveObserver(self.view2Observer)
    slicer.util.getNode('vtkMRMLViewNode3').RemoveObserver(self.view3Observer)

  #更新Tip位置
  def UpdateTip(self,unusedArg1=None, unusedArg2=None, unusedArg3=None):
    print('更新三维视图的label')
    View1Tip = slicer.app.layoutManager().threeDWidget('View1').threeDView().findChildren('QLabel')
    View2Tip = slicer.app.layoutManager().threeDWidget('View2').threeDView().findChildren('QLabel')
    View3Tip = slicer.app.layoutManager().threeDWidget('View3').threeDView().findChildren('QLabel')
    view1 =  slicer.app.layoutManager().threeDWidget('View1').threeDView()
    view2 =  slicer.app.layoutManager().threeDWidget('View2').threeDView()
    view3 =  slicer.app.layoutManager().threeDWidget('View3').threeDView()
    ViewTip = [View1Tip,View2Tip,View3Tip]
    SumPosition = [self.Position(view1),self.Position(view2),self.Position(view3)]
    for j in range (0,len(ViewTip)):
        for i in range (0,len(ViewTip[j])):                        
            Tip = ViewTip[j][i]
            index = int(Tip.objectName)-1
            position = SumPosition[j]
            Tip.setGeometry(position[index][0],position[index][1],position[index][2],position[index][3])
    print('更新完成')

  def Position(self,view):
    position = np.array([[view.width - 100, 25, 100, 40],
        [view.width - 100, 50, 100, 25],
        [0, view.height - 125, 100, 25],
        [0, view.height - 100, 100, 25],
        [0, view.height - 75, 100, 25],
        [0, view.height - 50, 100, 25],
        [5, 0.5 * view.height, 100, 40],
        [view.width - 100, 0.5 * view.height, 100, 40],
        [view.width - 100, view.height - 125, 100, 25],
        [view.width - 100, view.height - 100, 100, 25],
        [view.width - 100, view.height - 75, 100, 25],
        [view.width - 100, view.height - 50, 100, 25],
        [view.width - 100, 25, 100, 40],
        [view.width - 100, 50, 100, 25],
        [0.5*view.width, 25, 100, 40],
        [0.5*view.width, view.height-40, 100, 40]])
    return position 

  #--------------------------股骨------------------------------------------

  #为方便计算实时外翻角及屈膝角
  def AddSuiDongAxis(self):
      #股骨

    #防止重复添加
    ROIs = slicer.util.getNodesByClass('vtkMRMLTransformNode')
    Name = []
    for i in range(0, len(ROIs)):
      a = ROIs[i]
      Name.append(a.GetName())
    if '变换_1' in Name:
      return
    ras1, ras2, ras3, ras4 = [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]
    slicer.util.getNode('股骨头球心').GetNthFiducialPosition(0, ras1)
    slicer.util.getNode('开髓点').GetNthFiducialPosition(0, ras2)
    slicer.util.getNode('外侧凸点').GetNthFiducialPosition(0, ras3)
    slicer.util.getNode('内侧凹点').GetNthFiducialPosition(0, ras4)
    zb1 = [-ras1[0], -ras1[1], ras1[2]]  # 坐标1，球心
    zb2 = [-ras2[0], -ras2[1], ras2[2]]  # 坐标2，原点
    zb3 = [-ras3[0], -ras3[1], ras3[2]]  # 坐标3，左侧点
    zb4 = [-ras4[0], -ras4[1], ras4[2]]  # 坐标4，右侧点
    jxlz = [0, 0, 0]  # Y轴基向量
    for i in range(0, 3):
        jxlz[i] = zb1[i] - zb2[i]
    moz = np.sqrt(np.square(jxlz[0]) + np.square(jxlz[1]) + np.square(jxlz[2]))  # 基向量z的模
    for i in range(0, 3):
        jxlz[i] = jxlz[i] / moz
    csD = jxlz[0] * zb2[0] + jxlz[1] * zb2[1] + jxlz[2] * zb2[2]  # 平面方程参数D
    csT3 = (jxlz[0] * zb3[0] + jxlz[1] * zb3[1] + jxlz[2] * zb3[2] - csD) / (
            jxlz[0] * jxlz[0] + jxlz[1] * jxlz[1] + jxlz[2] * jxlz[2])  # 坐标3平面方程参数T
    ty3 = [0, 0, 0]  # 坐标3在YZ平面的投影
    for i in range(0, 3):
        ty3[i] = zb3[i] - jxlz[i] * csT3
    csT4 = (jxlz[0] * zb4[0] + jxlz[1] * zb4[1] + jxlz[2] * zb4[2] - csD) / (
            jxlz[0] * jxlz[0] + jxlz[1] * jxlz[1] + jxlz[2] * jxlz[2])
    ty4 = [0, 0, 0]
    for i in range(0, 3):
        ty4[i] = zb4[i] - jxlz[i] * csT4
    jxlx = [0, 0, 0]  # X轴基向量
    for i in range(0, 3):
        if slicer.modules.NoImageWelcomeWidget.judge == 'L':
            jxlx[i] = ty3[i] - ty4[i]
        else:
            jxlx[i] = ty4[i] - ty3[i]
    mox = np.sqrt(np.square(jxlx[0]) + np.square(jxlx[1]) + np.square(jxlx[2]))  # 基向量X的模
    for i in range(0, 3):
        jxlx[i] = jxlx[i] / mox
    jxly = [0, 0, 0]  # y轴基向量
    jxly[0] = -(jxlx[1] * jxlz[2] - jxlx[2] * jxlz[1])
    jxly[1] = -(jxlx[2] * jxlz[0] - jxlx[0] * jxlz[2])
    jxly[2] = -(jxlx[0] * jxlz[1] - jxlx[1] * jxlz[0])
    moy = np.sqrt(np.square(jxly[0]) + np.square(jxly[1]) + np.square(jxly[2]))  # 基向量y的模
    for i in range(0, 3):
        jxly[i] = jxly[i] / moy
    ccb = ([jxlx, jxly, jxlz])
    ccc = np.asarray(ccb)
    ccd = ccc.T
    np.savetxt(self.FilePath + "/Femur-jxl.txt", ccd, fmt='%6f')
    Ftrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    self.Ftrans2 = np.array([[float(jxlx[0]), float(jxly[0]), float(jxlz[0]), zb2[0]],
                            [float(jxlx[1]), float(jxly[1]), float(jxlz[1]), zb2[1]],
                            [float(jxlx[2]), float(jxly[2]), float(jxlz[2]), zb2[2]],
                            [0, 0, 0, 1]])
    Ftransform1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换')
    Ftransform2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_1')
    Ftransform1.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans1))
    Ftransform2.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(self.Ftrans2))
    Ftransform2.SetAndObserveTransformNodeID(Ftransform1.GetID())
    DianjiToTracker1=slicer.util.getNode("DianjiToTracker1")
    Ftransform1.SetAndObserveTransformNodeID(DianjiToTracker1.GetID())


    #胫骨
    ras1, ras2, ras3= [0, 0, 0], [0, 0, 0], [0, 0, 0]
    slicer.util.getNode('胫骨隆凸').GetNthFiducialPosition(0, ras1)
    slicer.util.getNode('胫骨结节').GetNthFiducialPosition(0, ras2)
    slicer.util.getNode('踝穴中心').GetNthFiducialPosition(0, ras3)
    Tzb1 = [-ras1[0], -ras1[1], ras1[2]]  # 坐标1，原点，髌骨近端的点
    Tzb2 = [-ras2[0], -ras2[1], ras2[2]]  # 坐标2，髌骨中间的点
    Tzb3 = [-ras3[0], -ras3[1], ras3[2]]  # 坐标2，髌骨远端的点
    Tjxlz = [0, 0, 0]  # z轴基向量
    for i in range(0, 3):
        Tjxlz[i] = Tzb1[i] - Tzb3[i]
    moz = np.sqrt(np.square(Tjxlz[0]) + np.square(Tjxlz[1]) + np.square(Tjxlz[2]))  # 基向量z的模
    for i in range(0, 3):
        Tjxlz[i] = Tjxlz[i] / moz
    TcsD = Tjxlz[0] * Tzb1[0] + Tjxlz[1] * Tzb1[1] + Tjxlz[2] * Tzb1[2]  # 平面方程参数D
    TcsT2 = (Tjxlz[0] * Tzb2[0] + Tjxlz[1] * Tzb2[1] + Tjxlz[2] * Tzb2[2] - TcsD) / (
            Tjxlz[0] * Tjxlz[0] + Tjxlz[1] * Tjxlz[1] + Tjxlz[2] * Tjxlz[2])  # 坐标3平面方程参数T
    Tty2 = [0, 0, 0]  # 坐标2在XY平面的投影
    for i in range(0, 3):
        Tty2[i] = Tzb2[i] - Tjxlz[i] * TcsT2
    Tjxly = [0, 0, 0]  # y轴基向量
    for i in range(0, 3):
        Tjxly[i] = Tzb1[i] - Tty2[i]
    moy = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量y的模
    for i in range(0, 3):
        Tjxly[i] = Tjxly[i] / moy
    Tjxlx = [0, 0, 0]  # x轴基向量
    Tjxlx[0] = -(Tjxlz[1] * Tjxly[2] - Tjxlz[2] * Tjxly[1])
    Tjxlx[1] = -(Tjxlz[2] * Tjxly[0] - Tjxlz[0] * Tjxly[2])
    Tjxlx[2] = -(Tjxlz[0] * Tjxly[1] - Tjxlz[1] * Tjxly[0])
    mox = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量x的模
    for i in range(0, 3):
        Tjxlx[i] = Tjxlx[i] / mox
    Tzb3xz = []
    jd = 1
    jd = math.radians(jd)
    zhjz = np.array([[Tjxlx[0], Tjxly[0], Tjxlz[0], Tzb1[0]], [Tjxlx[1], Tjxly[1], Tjxlz[1], Tzb1[1]],
            [Tjxlx[2], Tjxly[2], Tjxlz[2], Tzb1[2]], [0, 0, 0, 1]])
    Tzb3xz3 = self.GetMarix(zhjz,1,Tzb3)
    # for i in range(0, 3):
    #     Tzb3[i] = Tzb3xz3[i]
    Tjxlz = [0, 0, 0]  # z轴基向量
    for i in range(0, 3):
        Tjxlz[i] = Tzb1[i] - Tzb3[i]
    moz = np.sqrt(np.square(Tjxlz[0]) + np.square(Tjxlz[1]) + np.square(Tjxlz[2]))  # 基向量z的模
    for i in range(0, 3):
        Tjxlz[i] = Tjxlz[i] / moz
    TcsD = Tjxlz[0] * Tzb1[0] + Tjxlz[1] * Tzb1[1] + Tjxlz[2] * Tzb1[2]  # 平面方程参数D
    TcsT2 = (Tjxlz[0] * Tzb2[0] + Tjxlz[1] * Tzb2[1] + Tjxlz[2] * Tzb2[2] - TcsD) / (
            Tjxlz[0] * Tjxlz[0] + Tjxlz[1] * Tjxlz[1] + Tjxlz[2] * Tjxlz[2])  # 坐标3平面方程参数T
    Tty2 = [0, 0, 0]  # 坐标2在XY平面的投影
    for i in range(0, 3):
        Tty2[i] = Tzb2[i] - Tjxlz[i] * TcsT2
    Tjxly = [0, 0, 0]  # y轴基向量
    for i in range(0, 3):
        Tjxly[i] = Tzb1[i] - Tty2[i]
    moy = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量y的模
    for i in range(0, 3):
        Tjxly[i] = Tjxly[i] / moy
    Tjxlx = [0, 0, 0]  # X轴基向量
    Tjxlx[0] = -(Tjxlz[1] * Tjxly[2] - Tjxlz[2] * Tjxly[1])
    Tjxlx[1] = -(Tjxlz[2] * Tjxly[0] - Tjxlz[0] * Tjxly[2])
    Tjxlx[2] = -(Tjxlz[0] * Tjxly[1] - Tjxlz[1] * Tjxly[0])
    mox = np.sqrt(np.square(Tjxlx[0]) + np.square(Tjxlx[1]) + np.square(Tjxlx[2]))  # 基向量x的模
    for i in range(0, 3):
        Tjxlx[i] = Tjxlx[i] / mox
    ccb = ([Tjxlx, Tjxly, Tjxlz])
    ccc = np.asarray(ccb)
    ccd = ccc.T
    np.savetxt(self.FilePath + "/Tibia-jxl.txt", ccd, fmt='%6f')
    Ttrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    self.Ttrans2 = np.array([[float(Tjxlx[0]), float(Tjxly[0]), float(Tjxlz[0]), Tzb1[0]],
                            [float(Tjxlx[1]), float(Tjxly[1]), float(Tjxlz[1]), Tzb1[1]],
                            [float(Tjxlx[2]), float(Tjxly[2]), float(Tjxlz[2]), Tzb1[2]],
                            [0, 0, 0, 1]])
    Ttrans3 = np.array([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    Ttrans3_5 = np.array([[1, 0, 0, 9],
                        [0, 1, 0, -5],
                        [0, 0, 1, -10],
                        [0, 0, 0, 1]])
    Ttransform1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_3')
    Ttransform2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_4')
    Ttransform1.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ttrans1))
    Ttransform2.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(self.Ttrans2))
    Ttransform2.SetAndObserveTransformNodeID(Ttransform1.GetID())
    TibiaToTracker=slicer.util.getNode("TibiaToTracker")
    Ttransform1.SetAndObserveTransformNodeID(TibiaToTracker .GetID())
    o = [0, 0, 0]
    z = [0, 0, 1]
    y = [0, 1, 0]
    x = [1, 0, 0]
    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Femur_ZAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(z)
    Femur_ZAxis = slicer.util.getNode('变换_1')
    f.SetAndObserveTransformNodeID(Femur_ZAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_ZAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(z)
    Tibia_ZAxis = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_ZAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_XAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(x)
    Tibia_XAxis = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_XAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_YAxis')
    f.AddControlPoint(o)
    f.AddControlPoint(y)
    Tibia_YAxis = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_YAxis.GetID())
    f.SetDisplayVisibility(False)

    f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_YZPlane')
    f.AddControlPoint(o)
    f.AddControlPoint(y)
    f.AddControlPoint(z)
    Tibia_YZPlane = slicer.util.getNode('变换_4')
    f.SetAndObserveTransformNodeID(Tibia_YZPlane.GetID())
    f.SetDisplayVisibility(False)





  #股骨骨骼参数
  def onParameter(self):
    try:
      self.p1.clear()
      self.p1.close()
      self.p1.deleteLater()
      self.win.clear()
      self.win.close()
      self.win.deleteLater()
      slicer.mrmlScene.RemoveNode(slicer.util.getNode("TibiaLine"))
      slicer.mrmlScene.RemoveNode(slicer.util.getNode("FemurLine"))
      print("删除完了")
    
    except Exception as e:
      print(e)
      print("没删除")

    # self.CanShuImage()
    # self.ThreeDViewAndImageWidget(0)
    # for i in range (0,len(self.ui.GraphImage.children())):
    #   a = self.ui.GraphImage.children()[-1]
    #   a.delete() 

    # slicer.modules.noimageoperationimage.widgetRepresentation().setParent(self.noimageWidget)
    # # UI设置为与noImagewidget同宽高
    # slicer.modules.noimageoperationimage.widgetRepresentation().resize(self.noimageWidget.width, self.noimageWidget.height)
    # slicer.modules.noimageoperationimage.widgetRepresentation().show()

    # slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutTriple3DEndoscopyView)
    #self.ThreeDState()#三维视图状态正常
    # self.HideAll()#隐藏UI中的每一部分
    self.HidePart()#隐藏运行过程中产生的模型等
    print("paramenter 1")
    # self.ui.OperationPlanWidget.setVisible(True)#设置手术规划窗口可见
    # self.ui.GuGe.setVisible(True)#设置骨骼参数窗口可见
    # self.FemurButtonChecked(self.ui.Parameter)#设置当前选中的是骨骼参数按钮
    print("paramenter 2")
    #获取所有模型节点
    models = slicer.util.getNodesByClass('vtkMRMLModelNode')
    Name = []
    for i in range(0, len(models)):
      a = models[i]
      Name.append(a.GetName())
    ROIs = slicer.util.getNodesByClass('vtkMRMLMarkupsROINode')
    #加载的数据为工程文件
    if '股骨远端' in Name:
      self.HidePart()
      self.ShowNode('股骨远端')
     
    #加载的数据为患者数据
    else:
      self.ShowNode('Femur')
      if len(ROIs) < 5:
        ras1, ras2, ras3, ras4 = [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]
        slicer.util.getNode('股骨头球心').GetNthFiducialPosition(0, ras1)
        slicer.util.getNode('开髓点').GetNthFiducialPosition(0, ras2)
        slicer.util.getNode('外侧凸点').GetNthFiducialPosition(0, ras3)
        slicer.util.getNode('内侧凹点').GetNthFiducialPosition(0, ras4)
        zb1 = [ras1[0], ras1[1], ras1[2]]  # 坐标1，球心
        zb2 = [ras2[0], ras2[1], ras2[2]]  # 坐标2，原点
        zb3 = [ras3[0], ras3[1], ras3[2]]  # 坐标3，左侧点
        zb4 = [ras4[0], ras4[1], ras4[2]]  # 坐标4，右侧点
        jxlz = [0, 0, 0]  # Y轴基向量
        for i in range(0, 3):
            jxlz[i] = zb1[i] - zb2[i]
        moz = np.sqrt(np.square(jxlz[0]) + np.square(jxlz[1]) + np.square(jxlz[2]))  # 基向量z的模
        for i in range(0, 3):
            jxlz[i] = jxlz[i] / moz
        csD = jxlz[0] * zb2[0] + jxlz[1] * zb2[1] + jxlz[2] * zb2[2]  # 平面方程参数D
        csT3 = (jxlz[0] * zb3[0] + jxlz[1] * zb3[1] + jxlz[2] * zb3[2] - csD) / (
                jxlz[0] * jxlz[0] + jxlz[1] * jxlz[1] + jxlz[2] * jxlz[2])  # 坐标3平面方程参数T
        ty3 = [0, 0, 0]  # 坐标3在YZ平面的投影
        for i in range(0, 3):
            ty3[i] = zb3[i] - jxlz[i] * csT3
        csT4 = (jxlz[0] * zb4[0] + jxlz[1] * zb4[1] + jxlz[2] * zb4[2] - csD) / (
                jxlz[0] * jxlz[0] + jxlz[1] * jxlz[1] + jxlz[2] * jxlz[2])
        ty4 = [0, 0, 0]
        for i in range(0, 3):
            ty4[i] = zb4[i] - jxlz[i] * csT4
        jxlx = [0, 0, 0]  # X轴基向量
        for i in range(0, 3):#########判断左右腿
            if slicer.modules.NoImageWelcomeWidget.judge == 'L':
                jxlx[i] = ty3[i] - ty4[i]
            else:
                jxlx[i] = ty4[i] - ty3[i]
        mox = np.sqrt(np.square(jxlx[0]) + np.square(jxlx[1]) + np.square(jxlx[2]))  # 基向量X的模
        for i in range(0, 3):
            jxlx[i] = jxlx[i] / mox
        jxly = [0, 0, 0]  # y轴基向量
        jxly[0] = (jxlx[1] * jxlz[2] - jxlx[2] * jxlz[1])
        jxly[1] = (jxlx[2] * jxlz[0] - jxlx[0] * jxlz[2])
        jxly[2] = (jxlx[0] * jxlz[1] - jxlx[1] * jxlz[0])
        moy = np.sqrt(np.square(jxly[0]) + np.square(jxly[1]) + np.square(jxly[2]))  # 基向量y的模
        for i in range(0, 3):
            jxly[i] = jxly[i] / moy
        ccb = ([jxlx, jxly, jxlz])
        ccc = np.asarray(ccb)
        ccd = ccc.T
        #np.savetxt(self.FilePath + "/Femur-jxl.txt", ccd, fmt='%6f')
        Ftrans1 = np.array([[-1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])
        Ftrans2 = np.array([[float(jxlx[0]), float(jxly[0]), float(jxlz[0]), zb2[0]],
                                [float(jxlx[1]), float(jxly[1]), float(jxlz[1]), zb2[1]],
                                [float(jxlx[2]), float(jxly[2]), float(jxlz[2]), zb2[2]],
                                [0, 0, 0, 1]])
        self.Ftrans3=np.dot(Ftrans1,np.linalg.inv(Ftrans2))
        Ftrans4 = np.array([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])
        Ftrans5 = np.array([[1, 0, 0, 0],
                            [0, 1, 0, -9],
                            [0, 0, 1, 18],
                            [0, 0, 0, 1]])
        Ftransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_股骨临时')
        Ftransform1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_股骨约束')
        Ftransform2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_股骨调整')
        Ftransform3 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_股骨假体调整')
        Ftransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(self.Ftrans3))
        Ftransform1.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans4))
        Ftransform2.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans4))
        Ftransform3.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans5))
        Ftransform2.SetAndObserveTransformNodeID(Ftransform1.GetID())
        Ftransform1.SetAndObserveTransformNodeID(Ftransform3.GetID())
        inputModel = slicer.util.getNode('Femur')
        inputModel.SetAndObserveTransformNodeID(Ftransform.GetID())
        inputModel.HardenTransform()

        #将所有点复制出一份放到截骨调整中
        FemurPoints = ['H点','开髓点','内侧凹点','外侧凸点','内侧远端','外侧远端','内侧后髁','外侧后髁','外侧皮质高点','A点',"股骨头球心"]
        for i in range(len(FemurPoints)):
            PointNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', FemurPoints[i]+"1")
            point = [0, 0, 0]
            node1=slicer.util.getNode(FemurPoints[i]).GetNthControlPointPosition(0, point)
            point=[point[0],point[1],point[2],1]
            PointNode.AddControlPoint(np.dot(self.Ftrans3,point)[0:3])
            PointNode.SetAndObserveTransformNodeID(Ftransform2.GetID())
        roiNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsROINode', '股骨远端切割')
        roiNode.SetCenter([0, 0, 0])
        roiNode.SetSize([100, 100, 140])
        roiNode.SetDisplayVisibility(False)
        OutputModel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "股骨远端")
        inputModel = slicer.util.getNode('Femur')
        dynamicModelerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLDynamicModelerNode")
        dynamicModelerNode.SetToolName("ROI cut")
        dynamicModelerNode.SetNodeReferenceID("ROICut.InputModel", inputModel.GetID())
        dynamicModelerNode.SetNodeReferenceID("ROICut.InputROI", roiNode.GetID())
        dynamicModelerNode.SetNodeReferenceID("ROICut.OutputPositiveModel", OutputModel.GetID())
        # dynamicModelerNode.SetContinuousUpdate(1)
        dynamicModelerNode.SetAttribute("ROICut.CapSurface", '1')
        slicer.modules.dynamicmodeler.logic().RunDynamicModelerTool(dynamicModelerNode)
        self.NodeMove('股骨远端','变换_股骨调整')
        inputModel.SetDisplayVisibility(False)
        #self.addAxisFemur()
        #屈膝
        Ftrans6 = np.array([[1, 0, 0, 0],
                            [0, 1, 0, 9],
                            [0, 0, 1, -18],
                            [0, 0, 0, 1]])
        
        
        Ftrans7 = np.array([[1, 0, 0, 0],
                            [0, 0, -1, 13],
                            [0, 1, 0, 19],
                            [0, 0, 0, 1]])

        jtTo0_ni = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'jtTo0_ni')
        trans_quxi = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'trans_quxi')
        jtTo0 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'jtTo0')
        jtTo0_ni.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans5))
        trans_quxi.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans7))
        jtTo0.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ftrans6))
        trans_quxi.SetAndObserveTransformNodeID(jtTo0_ni.GetID())
        jtTo0.SetAndObserveTransformNodeID(trans_quxi.GetID())




    #根据参数智能推荐假体
    try:
      if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        self.SelectJiaTi('l')
        self.onFemurL(1)
      else:
        self.SelectJiaTi('R')
        self.onFemurR(1)
    except Exception as e:
      print(e)
    self.onParameter2()
    # #设置相机并居中
    # self.Camera1(self.view1)
    # self.Camera2(self.view2)
    # self.Camera3(self.view3)
    # self.view1.resetFocalPoint()
    # self.view2.resetFocalPoint()
    # self.view3.resetFocalPoint()
    # self.HidePart()
    # self.ShowNode('股骨远端')
    # self.ShowNode('胫骨近端')
    # self.ui.ModuleName.setText('手术规划')

  # def CanShuImage(self):
  #   APMLPath = os.path.join(self.iconsPath, 'APML.png')
  #   self.ui.APImage.setMaximumSize(200, 172)
  #   self.ui.APImage.setPixmap(qt.QPixmap(APMLPath))
  #   self.ui.APImage.setScaledContents(True)

  #   self.ui.MLImage.setPixmap(qt.QPixmap(APMLPath))
  #   self.ui.MLImage.setMaximumSize(200, 172)
  #   self.ui.MLImage.setScaledContents(True)

  #   self.ui.TibiaImage.setPixmap(qt.QPixmap(APMLPath))
  #   self.ui.TibiaImage.setMaximumSize(200, 172)
  #   self.ui.TibiaImage.setScaledContents(True)
  
  #获取第一刀截骨面(根据内侧远端到第一截骨面的距离确定)
  #股骨屈膝
  def ChangeJtStatueToQuxi(self,ifQuxi):
      trans_femur=slicer.util.getNode("变换_股骨假体调整")
      if slicer.modules.NoImageWelcomeWidget.judge == 'L':
        femurJtName=self.FemurL
      else:
        femurJtName=self.FemurR
      jt=slicer.util.getNode(femurJtName)
      trans=slicer.util.getNode("jtTo0")
      if ifQuxi:
        trans_femur.SetAndObserveTransformNodeID(trans.GetID())
        jt.SetAndObserveTransformNodeID(trans.GetID())
        slicer.modules.popup.widgetRepresentation().self().onConfirm()
      else:
        trans_femur.SetAndObserveTransformNodeID(None)
        jt.SetAndObserveTransformNodeID(None)
        slicer.modules.popup.widgetRepresentation().self().onConfirm()

  def FirstJieGu(self):
      point = [0, 0, 0]
      point1 = [0,0,0]
      slicer.util.getNode('内侧远端1').GetNthControlPointPositionWorld(0, point)
      slicer.util.getNode('外侧皮质高点1').GetNthControlPointPositionWorld(0, point1)
      transformR = slicer.util.getNode('变换_股骨假体调整')
      Femur1JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第一截骨面')
      Femur1JieGu.AddControlPoint(15.063, 25, 0)
      Femur1JieGu.AddControlPoint(0, 0, 0)
      Femur1JieGu.AddControlPoint(-21.372, -23.271, 0)
      Femur1JieGu.SetAndObserveTransformNodeID(transformR.GetID())
      Femur2JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第二截骨面')
      Femur2JieGu.AddControlPoint(-15.063, 23.063, 22.222)
      Femur2JieGu.AddControlPoint(1.143, 23.207, 29.894)
      Femur2JieGu.AddControlPoint(21.372, 23.271, 24.171)
      Femur2JieGu.SetAndObserveTransformNodeID(transformR.GetID())
      # 隐藏股骨第一截骨面的点
      self.HideNode('股骨第一截骨面')
      self.HideNode('股骨第二截骨面')
      Femur1JGM = self.GetTransPoint('股骨第一截骨面')
      Femur2JGM = self.GetTransPoint('股骨第二截骨面')
      d =self.point2area_distance(Femur1JGM,point)
      d1 = self.point2area_distance(Femur2JGM,point1)
      self.destance = d-8
      FtransTmp = np.array([[1, 0, 0, 2],
                          [0, 1, 0, d1+3],
                          [0, 0, 1, self.destance],
                          [0, 0, 0, 1]])
      FtransformTmp = slicer.util.getNode('变换_股骨约束')
      FtransformTmp.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FtransTmp))

  #获取上层变换的合集
  def FemurTrans(self):
    transform = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换'))
    transform1 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_1'))
    transform2 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_2'))
    transform_tmp = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_临时'))
    Trans = np.dot(np.dot(np.dot(transform, transform1), transform_tmp),transform2)
    return Trans
  #推荐股骨假体    
  def SelectJiaTi(self, judge):
      self.FirstJieGu()
      PointPath = os.path.join(os.path.dirname(__file__), '假体库/a')
      point1 = [0, 0, 0]
      point2 = [0,0,0]
      slicer.util.getNode('外侧皮质高点1').GetNthControlPointPositionWorld(0, point1)
      slicer.util.getNode('外侧后髁1').GetNthControlPointPositionWorld(0, point2)
      #trans = self.FemurTrans()

      #骨骼纵向高度 （算上软骨2mm）
      height = abs(point1[1] - point2[1])-6
      #self.ui.AP.setText(height)
      self.select = 0
      #假体纵向高度
      list = [35.69, 38.69, 41.09, 43.69, 47.59, 50.07]
      
      #假体型号
      list3 = ['1-5', '2', '2-5', '3', '4', '5']
      Femur1JGM = self.GetTransPoint('股骨第一截骨面')
      #皮质高点到第一刀截骨面的距离
      ras1 = [0, 0, 0]
      slicer.util.getNode('外侧皮质高点1').GetNthControlPointPositionWorld(0, ras1)
      d = self.point2area_distance(Femur1JGM, ras1)
      #第二刀倾斜角为6°
      k=math.tan(math.radians(6))
      judge1=[]
      index1=[]
      b1 = 0
      for i in range(0, len(list)):
        inputPoints=[]
        rang = k*d + list[i]
        # self.ui.tableWidget.setItem(i, 0, qt.QTableWidgetItem(str(rang)))
        if rang < height:
          name = 'femur-' + judge + list3[i]
          lujing = os.path.join(PointPath,name+'.txt')
          print('lujing',lujing)
          inputPoints  =  np.loadtxt(lujing) 
          TransformTmp = slicer.util.getNode('变换_股骨约束')
          trans = slicer.util.arrayFromTransformMatrix(TransformTmp)
          trans_ni=np.linalg.inv(trans)
          for j in range(len(inputPoints)):
            inputPoints[j]=np.dot(trans_ni,[inputPoints[j][0],inputPoints[j][1],inputPoints[j][2],1])[0:3]

          
          inputModel=slicer.util.getNode('Femur')
          surface_World = inputModel.GetPolyData()
          distanceFilter = vtk.vtkImplicitPolyDataDistance()
          distanceFilter.SetInput(surface_World)
          nOfFiducialPoints = 8
          distances = np.zeros(nOfFiducialPoints)
          for j in range(nOfFiducialPoints):
            point_World = inputPoints[j]
            closestPointOnSurface_World = np.zeros(3)
            closestPointDistance = distanceFilter.EvaluateFunctionAndGetClosestPoint(point_World, closestPointOnSurface_World)
            distances[j] = closestPointDistance
          
          print('distances:',distances)
          a=0
          if i == 0:
            b1=distances[0]

          if distances[0]+distances[4]<0 and  distances[1]+distances[5]<0 and distances[2]+distances[6]<0 and distances[3]+distances[7]<0:
            a=8

          if a==8:
            sum = 0
            for j in range(nOfFiducialPoints):
              sum =sum + distances[j]
            judge1.append(sum)        
            index1.append(i)
        try:
          max_judge1=judge1.index(max(judge1))
          self.select = index1[max_judge1]
        except:
          self.select = 2

      if len(judge1)<1 :
        self.select = 2

      Name = 'femur-'+judge+list3[self.select]
      #self.ui.JiaTiName.setText(Name)

          
      if judge == 'l':
        knee = '左侧'
        # self.ui.FemurL.setCurrentText(Name)
        self.FemurL = Name

      else:
        knee = '右侧'
        # self.ui.FemurR.setCurrentText(Name)
        self.FemurR = Name
          
      #self.ui.knee.setText(knee)
      MLList=[57.000999450683594, 60.0, 63.0, 66.0, 71.0, 73.0000991821289]
      # for i in range(0,len(MLList)):
        # self.ui.tableWidget.setItem(i, 1, qt.QTableWidgetItem(str(MLList[i])))
      # if len(index1)==0:
      #   self.ui.ML.setText(str(MLList[len(index1)]-np.abs(b1)/10))
      #   print(len(index1))
      # else: 
      #   self.ui.ML.setText(str(MLList[len(index1)-1]+np.abs(b1)/10))
      #   print(len(index1))
      #for i in range(0,len(index1)):
      # self.ui.tableWidget.item(len(index1)-1, 0).setBackground(qt.QColor(124, 189, 39))
      # self.ui.tableWidget.item(len(index1)-1,1).setBackground(qt.QColor(124, 189, 39))


  #加载股骨假体           
  def loadJiaTi(self, name):
    try:
        slicer.mrmlScene.RemoveNode(self.jiatiload)
    except Exception as e:
        print(e) 
    lujing = os.path.join(self.jiatiPath, name + '.stl')
    self.jiatiload = slicer.util.loadModel(lujing)
    self.jiatiload.SetName(name)
    #股骨切割
    
    #将假体放在FTransformR变换下：
    #FtransformR = slicer.util.getNode('变换_股骨假体调整')
    #self.jiatiload.SetAndObserveTransformNodeID(FtransformR.GetID())
    self.loaddier()
    slicer.modules.popup.widgetRepresentation().self().onConfirm()
    if self.ui.pushButton_52.checked:
      trans=slicer.util.getNode("jtTo0")
      jt = slicer.util.getNode(name)
      jt.SetAndObserveTransformNodeID(trans.GetID())

  #在世界坐标系下求点的坐标
  def QiuDianInTop(self, name):
    ras1 = [0, 0, 0]
    slicer.util.getNode(name).GetNthControlPointPositionWorld(0, ras1)
    transNode = slicer.util.getNode('DianjiToTracker1')
    trans0 = slicer.util.arrayFromTransformMatrix(transNode)
    transformNode = slicer.util.getNode('变换')
    trans = slicer.util.arrayFromTransformMatrix(transformNode)
    transformNode1 = slicer.util.getNode('变换_1')
    trans1 = slicer.util.arrayFromTransformMatrix(transformNode1)
    trans2=np.dot(np.dot(trans0,trans),trans1)
    Trans_ni=np.linalg.inv(trans2)
    point = np.array([ras1[0],ras1[1],ras1[2],1])
    point2 = np.dot(point,Trans_ni)
    return point2
    
  def get_point_femur_to_ras(self,p):
    # 股骨变换
    transformNode = slicer.util.getNode('变换')
    trans = slicer.util.arrayFromTransformMatrix(transformNode)
    transformNode1 = slicer.util.getNode('变换_1')
    trans1 = slicer.util.arrayFromTransformMatrix(transformNode1)
    transformNodeTmp = slicer.util.getNode('变换_临时')
    transTmp = slicer.util.arrayFromTransformMatrix(transformNodeTmp)
    transformNode2 = slicer.util.getNode('变换_2')
    trans2 = slicer.util.arrayFromTransformMatrix(transformNode2)
    transformNodeR = slicer.util.getNode('变换_R')
    transR = slicer.util.arrayFromTransformMatrix(transformNodeR)
    FemurTrans = np.dot(np.dot(np.dot(np.dot(trans, trans1), transTmp), trans2), transR)
    FemurTrans_ni = np.linalg.inv(FemurTrans)
    point=np.array([p[0],p[1],p[2],1])
    point=np.dot(FemurTrans_ni,point)
    return point[0:3]

  def YueShu(self):
    import math
    ras = [0, 0, 0]
    ras1 = [0, 0, 0]
    slicer.util.getNode('内侧远端1').GetNthControlPointPositionWorld(0, ras)
    Femur1JGM = self.GetTransPoint('股骨第一截骨面')
    position=self.point2area_distance(Femur1JGM, ras)
    distance = position-8
    transformR = slicer.util.getNode('变换_股骨约束')
    a =slicer.util.arrayFromTransformMatrix(transformR)
    FtransTmp = np.array([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, distance],
                        [0, 0, 0, 1]])
    trans = np.dot(a,FtransTmp)
    transformR.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans))
    print('distance 赋值完成')
    Femur2JGM = self.GetTransPoint('股骨第二截骨面')
    slicer.util.getNode('外侧皮质高点1').GetNthControlPointPositionWorld(0, ras1)
    #根据外侧皮质高点在第二刀切面的位置来判断调整正负
    slicer.util.getNode('内侧远端1').GetNthControlPointPositionWorld(0, ras)
    #t_tibia = self.Ftrans2
    #n1=[t_tibia[0][1], t_tibia[1][1], t_tibia[2][1]]
    n1=[0,1,0]
    n2 = np.array(ras1) - self.TouYing(Femur2JGM, ras1)
    if np.dot(n1,n2)<0:
        direction = 1
    else:
        direction = -1
    d = self.point2area_distance(Femur2JGM, ras1)
    x = d/math.cos(math.radians(6))
    #direction = slicer.modules.PopupWidget.direction
    x = direction *x
    a =slicer.util.arrayFromTransformMatrix(transformR)

    FtransTmp = np.array([[1, 0, 0, 0],
                        [0, 1, 0, x],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    trans = np.dot(a,FtransTmp)
    transformR.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans))
    print(trans)
    print('所有矩阵赋值完成')
    self.loaddisan()



  #加载股骨第二截骨面
  def loaddier(self):
    # 第二刀截骨面
    FtransformR = slicer.util.getNode('变换_股骨假体调整')
    segs = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
    Name = []

    for i in range(0, len(segs)):
        a = segs[i]
        Name.append(a.GetName())
    if '股骨第二截骨面' in Name:
        slicer.mrmlScene.RemoveNode(slicer.util.getNode('股骨第二截骨面'))
    
    FtransTmp = np.array([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, self.destance],
                        [0, 0, 0, 1]])
    FtransformTmp = slicer.util.getNode('变换_股骨约束')
    FtransformTmp.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FtransTmp))

    if self.jiatiload.GetName() == 'femur-R1-5' or self.jiatiload.GetName() == 'femur-l1-5':

        Femur2JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第二截骨面')
        Femur2JieGu.AddControlPoint(-15.063, 23.063, 22.222)
        Femur2JieGu.AddControlPoint(1.143, 23.207, 29.894)
        Femur2JieGu.AddControlPoint(21.372, 23.271, 24.171)

    elif self.jiatiload.GetName() == 'femur-R2' or self.jiatiload.GetName() == 'femur-l2':

        Femur2JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第二截骨面')
        Femur2JieGu.AddControlPoint(-16.637, 24.306, 21.857)
        Femur2JieGu.AddControlPoint(1.185, 25.471, 32.778)
        Femur2JieGu.AddControlPoint(22.742, 24.575, 24.382)

    elif self.jiatiload.GetName() == 'femur-R2-5' or self.jiatiload.GetName() == 'femur-l2-5':

        Femur2JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第二截骨面')
        Femur2JieGu.AddControlPoint(-17.709, 25.954, 22.334)
        Femur2JieGu.AddControlPoint(1.430, 27.379, 35.696)
        Femur2JieGu.AddControlPoint(24.282, 26.237, 24.987)

    elif self.jiatiload.GetName() == 'femur-R3' or self.jiatiload.GetName() == 'femur-l3':

        Femur2JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第二截骨面')
        Femur2JieGu.AddControlPoint(-18.255, 27.746, 22.792)
        Femur2JieGu.AddControlPoint(1.727, 29.360, 37.930)
        Femur2JieGu.AddControlPoint(25.269, 28.035, 25.497)

    elif self.jiatiload.GetName() == 'femur-R4' or self.jiatiload.GetName() == 'femur-l4':

        Femur2JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第二截骨面')
        Femur2JieGu.AddControlPoint(-19.597, 30.070, 23.700)
        Femur2JieGu.AddControlPoint(2.089, 32.049, 42.257)
        Femur2JieGu.AddControlPoint(27.321, 30.453, 27.293)

    elif self.jiatiload.GetName() == 'femur-R5' or self.jiatiload.GetName() == 'femur-l5':

        Femur2JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第二截骨面')
        Femur2JieGu.AddControlPoint(-19.941, 30.642, 24.760)
        Femur2JieGu.AddControlPoint(2.089, 32.049, 42.257)
        Femur2JieGu.AddControlPoint(27.877, 31.025, 28.357)

    Femur2JieGu.SetAndObserveTransformNodeID(FtransformR.GetID())
    # 隐藏股骨第二截骨面的点
    self.HideNode('股骨第二截骨面')
    Femur2JGM = self.GetTransPoint('股骨第二截骨面')
    # Femur2JGM[0]=self.getPointsInTrans(1,Femur2JGM[0])
    # Femur2JGM[1]=self.getPointsInTrans(1,Femur2JGM[1])
    # Femur2JGM[2]=self.getPointsInTrans(1,Femur2JGM[2])
    try:
      ras1 = [0, 0, 0]
      slicer.util.getNode('外侧皮质高点1').GetNthControlPointPositionWorld(0, ras1)
      d = self.point2area_distance(Femur2JGM, ras1)
      x = d/math.cos(math.radians(6))
      self.record = x
      FtransTmp = np.array([[1, 0, 0, 0],
              [0, 1, 0, x],
              [0, 0, 1, self.destance],
              [0, 0, 0, 1]])
      FtransformTmp.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FtransTmp))
    except Exception as e:
      print(e)
    self.loaddisan()

  def loaddisan(self):
    # 第三刀截骨面
    TransformR = slicer.util.getNode('变换_股骨假体调整')
    segs = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
    Name = []
    for i in range(0, len(segs)):
        a = segs[i]
        Name.append(a.GetName())
    if '股骨第三截骨面' in Name:
      slicer.mrmlScene.RemoveNode(slicer.util.getNode('股骨第三截骨面'))
    Femur3JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第三截骨面')
    if self.jiatiload.GetName() == 'femur-R1-5' or self.jiatiload.GetName() == 'femur-l1-5':
      Femur3JieGu.AddControlPoint(27.557, -16.002, 11.971)
      Femur3JieGu.AddControlPoint(11.793, -16.055, 15.009)
      Femur3JieGu.AddControlPoint(-27.508, -15.977, 10.607)
    elif self.jiatiload.GetName() == 'femur-R2' or self.jiatiload.GetName() == 'femur-l2':
      Femur3JieGu.AddControlPoint(28.561, -17.734, 13.564)
      Femur3JieGu.AddControlPoint(11.861, -17.780, 16.172)
      Femur3JieGu.AddControlPoint(-28.927, -17.695, 11.328)
    elif self.jiatiload.GetName() == 'femur-R2-5' or self.jiatiload.GetName() == 'femur-l2-5':
      Femur3JieGu.AddControlPoint(30.390, -18.590, 16.982)
      Femur3JieGu.AddControlPoint(11.778, -18.497, 11.740)
      Femur3JieGu.AddControlPoint(-30.265, -18.453, 9.234)
    elif self.jiatiload.GetName() == 'femur-R3' or self.jiatiload.GetName() == 'femur-l3':
      Femur3JieGu.AddControlPoint(32.234, -19.490, 15.771)
      Femur3JieGu.AddControlPoint(11.778, -18.497, 11.740)
      Femur3JieGu.AddControlPoint(-31.921, -19.462, 14.190)
    elif self.jiatiload.GetName() == 'femur-R4' or self.jiatiload.GetName() == 'femur-l4':
      Femur3JieGu.AddControlPoint(34.653, -20.921, 11.327)
      Femur3JieGu.AddControlPoint(12.011, -20.998, 15.694)
      Femur3JieGu.AddControlPoint(-34.498, -21.007, 16.178)
    elif self.jiatiload.GetName() == 'femur-R5' or self.jiatiload.GetName() == 'femur-l5':
      Femur3JieGu.AddControlPoint(35.419, -23.102, 13.337)
      Femur3JieGu.AddControlPoint(11.893, -23.144, 15.654)
      Femur3JieGu.AddControlPoint(-35.384, -23.198, 18.747)
    Femur3JieGu.SetAndObserveTransformNodeID(TransformR.GetID())
    # 隐藏股骨第三截骨面的点
    self.HideNode('股骨第三截骨面')


  # 股骨截骨调整
  def onAdjustment(self):
    # rotationTransformNode = slicer.util.getNode('DianjiToTracker1')
    # try:
    #   rotationTransformNode.RemoveObserver(self.updataForceAngle)
    # except:
    #   pass
    try:
      slicer.mrmlScene.RemoveNode(slicer.util.getNode("TibiaLine"))
      slicer.mrmlScene.RemoveNode(slicer.util.getNode("FemurLine"))
    except:
      pass


    # 第三刀截骨面
    TransformR = slicer.util.getNode('变换_股骨假体调整')
    segs = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
    Name = []

    for i in range(0, len(segs)):
        a = segs[i]
        Name.append(a.GetName())
    if '股骨第三截骨面' in Name:
      slicer.mrmlScene.RemoveNode(slicer.util.getNode('股骨第三截骨面'))

    Femur3JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '股骨第三截骨面')
    if self.jiatiload.GetName() == 'femur-R1-5' or self.jiatiload.GetName() == 'femur-l1-5':
      Femur3JieGu.AddControlPoint(27.557, -16.002, 11.971)
      Femur3JieGu.AddControlPoint(11.793, -16.055, 15.009)
      Femur3JieGu.AddControlPoint(-27.508, -15.977, 10.607)
    elif self.jiatiload.GetName() == 'femur-R2' or self.jiatiload.GetName() == 'femur-l2':
      Femur3JieGu.AddControlPoint(28.561, -17.734, 13.564)
      Femur3JieGu.AddControlPoint(11.861, -17.780, 16.172)
      Femur3JieGu.AddControlPoint(-28.927, -17.695, 11.328)
    elif self.jiatiload.GetName() == 'femur-R2-5' or self.jiatiload.GetName() == 'femur-l2-5':
      Femur3JieGu.AddControlPoint(30.390, -18.590, 16.982)
      Femur3JieGu.AddControlPoint(11.778, -18.497, 11.740)
      Femur3JieGu.AddControlPoint(-30.265, -18.453, 9.234)
    elif self.jiatiload.GetName() == 'femur-R3' or self.jiatiload.GetName() == 'femur-l3':
      Femur3JieGu.AddControlPoint(32.234, -19.490, 15.771)
      Femur3JieGu.AddControlPoint(11.778, -18.497, 11.740)
      Femur3JieGu.AddControlPoint(-31.921, -19.462, 14.190)
    elif self.jiatiload.GetName() == 'femur-R4' or self.jiatiload.GetName() == 'femur-l4':
      Femur3JieGu.AddControlPoint(34.653, -20.921, 11.327)
      Femur3JieGu.AddControlPoint(12.011, -20.998, 15.694)
      Femur3JieGu.AddControlPoint(-34.498, -21.007, 16.178)
    elif self.jiatiload.GetName() == 'femur-R5' or self.jiatiload.GetName() == 'femur-l5':
      Femur3JieGu.AddControlPoint(35.419, -23.102, 13.337)
      Femur3JieGu.AddControlPoint(11.893, -23.144, 15.654)
      Femur3JieGu.AddControlPoint(-35.384, -23.198, 18.747)

    Femur3JieGu.SetAndObserveTransformNodeID(TransformR.GetID())
    # 隐藏股骨第三截骨面的点
    self.HideNode('股骨第三截骨面')

    # -----------------S----------------------------------
    # 计算角度
    # ---------------------------------------------------
    try:
      ras1, ras2, ras3, ras4 = [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0],
      ras5, ras6, ras7 = [0, 0, 0], [0, 0, 0], [0, 0, 0]
      slicer.util.getNode('股骨头球心1').GetNthControlPointPositionWorld(0, ras1)
      slicer.util.getNode('开髓点1').GetNthControlPointPositionWorld(0, ras2)
      slicer.util.getNode('外侧凸点1').GetNthControlPointPositionWorld(0, ras3)
      slicer.util.getNode('内侧凹点1').GetNthControlPointPositionWorld(0, ras4)
      slicer.util.getNode('H点1').GetNthControlPointPositionWorld(0, ras5)
      slicer.util.getNode('内侧后髁1').GetNthControlPointPositionWorld(0, ras6)
      slicer.util.getNode('外侧后髁1').GetNthControlPointPositionWorld(0, ras7)

      # 外翻角
      xl1 = [ras1[0] - ras2[0], ras1[1] - ras2[1], ras1[2] - ras2[2]]
      xl2 = [ras5[0] - ras2[0], ras5[1] - ras2[1], ras5[2] - ras2[2]]
      self.WaiFanJiao = self.Angle(xl1, xl2)

      # 外旋角
      FemurJGM= self.GetTransPoint('股骨第一截骨面')
      NeiAoTY = self.TouYing(FemurJGM, ras4)
      WaiTuTY = self.TouYing(FemurJGM, ras3)
      NeiKeTY = self.TouYing(FemurJGM, ras6)
      WaiKeTY = self.TouYing(FemurJGM, ras7)

      xl3 = np.array([WaiTuTY[0] - NeiAoTY[0], WaiTuTY[1] - NeiAoTY[1], WaiTuTY[2] - NeiAoTY[2]])
      xl4 = np.array([WaiKeTY[0] - NeiKeTY[0], WaiKeTY[1] - NeiKeTY[1], WaiKeTY[2] - NeiKeTY[2]])
      waixuanjiao = self.Angle(xl3, xl4)
      self.WaiXuanJiao = waixuanjiao

    except Exception as e:
      print(e)
    






  #股骨三维视图注释
  def FemurCameraTip(self):
    self.hideInformation()#删除掉之前视图上的内容
    #视图1按钮
    icon1A = qt.QIcon()
    icons1APath = os.path.join(self.iconsPath, '重置.png')
    icon1A.addPixmap(qt.QPixmap(icons1APath))
    self.V1Button = qt.QPushButton(self.view1)
    self.V1Button.setGeometry(5, 5, 50, 50)
    self.V1Button.setIconSize(qt.QSize(60, 60))
    self.V1Button.setIcon(icon1A)
    self.V1Button.setFlat(True)
    self.V1Button.setStyleSheet("QPushButton{border:none;background:transparent;color:transparent;}")
    self.V1Button.connect('clicked(bool)',self.onV1Button)
    self.V1Button.setToolTip('锁定')
    self.V1Button.show()
    # -------------------------------------------------------------------------------------------------------
    #视图2按钮
    icon2A = qt.QIcon()
    icons2APath = os.path.join(self.iconsPath, '箭头.png')
    icon2A.addPixmap(qt.QPixmap(icons2APath))
    self.V2Button = qt.QPushButton(self.view2)
    self.V2Button.setGeometry(5, 5, 41, 41)
    self.V2Button.setIconSize(qt.QSize(41, 41))
    self.V2Button.setIcon(icon2A)
    self.V2Button.setFlat(True)
    self.V2Button.setStyleSheet("QPushButton{border:none;background:transparent;}")
    self.V2Button.connect('clicked(bool)', self.onV2Button)
    self.V2Button.show()

    # ---------------------------------------------------------------------------------------------------------
    #视图3按钮
    icon3A = qt.QIcon()
    icons3APath = os.path.join(self.iconsPath, '箭头.png')
    icon3A.addPixmap(qt.QPixmap(icons3APath))
    self.V3Button = qt.QPushButton(self.view3)
    self.V3Button.setGeometry(5, 5, 46, 46)
    self.V3Button.setIconSize(qt.QSize(46, 46))
    self.V3Button.setIcon(icon3A)
    self.V3Button.setFlat(True)
    self.V3Button.setStyleSheet("QPushButton{border:none;background:transparent;}")
    self.V3Button.connect('clicked(bool)', self.onV3Button)
    self.V3Button.show()
    self.Camera1(self.view1)
    self.Camera2(self.view2)
    self.Camera3(self.view3)
    cameraNode=self.view1.cameraNode()
    cameraNode2 = self.view2.cameraNode()

    #显示每个视图的注释
    # 左腿
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      if (cameraNode.GetName() == 'FC1'):
        if (cameraNode2.GetName() == 'FC2'):
          self.Camera1Tip(self.view1)
          self.Camera2Tip(self.view2)
          self.Camera3Tip(self.view3)
        else:
          self.Camera1Tip(self.view1)
          self.Camera2Tip(self.view3)
          self.Camera3Tip(self.view2)

      elif (cameraNode.GetName() == 'FC2'):
        if (cameraNode2.GetName() == 'FC1'):
          self.Camera1Tip(self.view2)
          self.Camera2Tip(self.view1)
          self.Camera3Tip(self.view3)
        else:
          self.Camera1Tip(self.view2)
          self.Camera2Tip(self.view3)
          self.Camera3Tip(self.view1)
      else:
          if (cameraNode2.GetName() == 'FC2'):
            self.Camera1Tip(self.view3)
            self.Camera2Tip(self.view2)
            self.Camera3Tip(self.view1)
          else:
            self.Camera1Tip(self.view3)
            self.Camera2Tip(self.view1)
            self.Camera3Tip(self.view2)
    else:
      if (cameraNode.GetName() == 'FC1'):
        if (cameraNode2.GetName() == 'FC2'):
          self.Camera1TipRight(self.view1)
          self.Camera2Tip(self.view2)
          self.Camera3TipRight(self.view3)
        else:
          self.Camera1TipRight(self.view1)
          self.Camera2Tip(self.view3)
          self.Camera3TipRight(self.view2)
      elif (cameraNode.GetName() == 'FC2'):
        if (cameraNode2.GetName() == 'FC1'):
          self.Camera1TipRight(self.view2)
          self.Camera2Tip(self.view1)
          self.Camera3TipRight(self.view3)
        else:
          self.Camera1TipRight(self.view2)
          self.Camera2Tip(self.view3)
          self.Camera3TipRight(self.view1)
      else:
        if (cameraNode2.GetName() == 'FC2'):
          self.Camera1TipRight(self.view3)
          self.Camera2Tip(self.view2)
          self.Camera3TipRight(self.view1)
        else:
          self.Camera1TipRight(self.view3)
          self.Camera2Tip(self.view1)
          self.Camera3TipRight(self.view2)

  #股骨视图选择
  def onViewSelect(self):
    rotationTransformNode = slicer.util.getNode('DianjiToTracker1')
    try:
      rotationTransformNode.RemoveObserver(self.ZuiDiDian)
    except:
      pass
    try:
      slicer.mrmlScene.RemoveNode(slicer.util.getNode('OutSide'))
      slicer.mrmlScene.RemoveNode(slicer.util.getNode('InSide'))
      slicer.mrmlScene.RemoveNode(self.JieGuJianXi)
    except:
      pass
    self.HideAll()
    self.ui.PopupWidget.setVisible(True)
    self.hideInformation()
    self.ThreeDState()
    self.ui.PopupWidget.setMinimumHeight(650)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutTriple3DEndoscopyView)    
    slicer.modules.viewselect.widgetRepresentation().setParent(self.ui.PopupWidget)
    layout = qt.QHBoxLayout()
    layout.addWidget(slicer.modules.viewselect.widgetRepresentation())
    self.ui.PopupWidget.setLayout(layout)
    #slicer.modules.viewselect.widgetRepresentation().setGeometry(-10,-10,624,800)
    slicer.modules.viewselect.widgetRepresentation().show()
    # self.FemurButtonChecked(self.ui.ViewChoose)
    # self.TibiaButtonChecked(self.ui.ViewChoose2)
    # self.ui.ModuleName.setText('手术规划')
  # #重置
  # def onReset(self):
  #   message = qt.QMessageBox(qt.QMessageBox.Information,'重置',"是否要重置规划的方案？",qt.QMessageBox.Ok|qt.QMessageBox.Cancel)
  #   message.button(qt.QMessageBox().Ok).setText('是')
  #   message.button(qt.QMessageBox().Cancel).setText('否')
  #   c= message.exec()
  #   if c == qt.QMessageBox.Ok:
  #     # self.FemurButtonChecked(self.ui.Reset)
  #     # self.TibiaButtonChecked(self.ui.ReSet2)
  #     slicer.app.setOverrideCursor(qt.Qt.WaitCursor)  # 光标变成圆圈
  #     self.DeleteNode('变换')
  #     self.DeleteNode('变换_1')
  #     self.DeleteNode('变换_2')
  #     self.DeleteNode('变换_临时')
  #     self.DeleteNode('变换_R')
  #     self.DeleteNode(self.jiatiload.GetName())
  #     self.DeleteNode('股骨远端切割')
  #     self.DeleteNode('股骨第一截骨面')
  #     self.DeleteNode('股骨第二截骨面')
  #     self.DeleteNode('股骨第三截骨面')
  #     self.DeleteNode('DynamicModeler')
  #     self.DeleteNode('股骨远端')
  #     self.DeleteNode('切割1')
  #     self.DeleteNode('切割2')
  #     self.DeleteNode('切割3')
  #     self.DeleteNode('切割4')
  #     self.DeleteNode('切割5')
  #     self.DeleteNode('部件1')
  #     self.DeleteNode('部件2')
  #     self.DeleteNode('部件3')
  #     self.DeleteNode('部件4')
  #     self.DeleteNode('部件5')
  #     self.DeleteNode('动态切割1')
  #     self.DeleteNode('动态切割2')
  #     self.DeleteNode('动态切割3')
  #     self.DeleteNode('动态切割4')
  #     self.DeleteNode('动态切割5')
  #     self.DeleteNode('股骨切割')
  #     self.DeleteNode('变换_3')
  #     self.DeleteNode('变换_4')
  #     self.DeleteNode('变换_5')
  #     self.DeleteNode('变换_胫骨')
  #     self.DeleteNode('变换_约束')
  #     self.DeleteNode(self.TibiaJiaTiload.GetName())
  #     self.DeleteNode('胫骨近端切割')
  #     self.DeleteNode('胫骨截骨面')
  #     self.DeleteNode('胫骨近端')
  #     self.DeleteNode('DynamicModeler_1')
  #     self.DeleteNode('胫骨切割')
  #     self.DeleteNode('切割6')
  #     self.DeleteNode('部件6')
  #     self.DeleteNode('动态切割6')
  #     slicer.app.restoreOverrideCursor()  # 变回光标原来的形状

  #     # #显示所有的点
  #     # self.ShowNode('A点')
  #     # self.ShowNode('内侧后髁')
  #     # self.ShowNode('外侧后髁')
  #     # self.ShowNode('外侧远端')
  #     # self.ShowNode('内侧远端')
  #     # self.ShowNode('外侧凸点')
  #     # self.ShowNode('内侧凹点')
  #     # self.ShowNode('外侧皮质高点')
  #     # self.ShowNode('开髓点')
  #     # self.ShowNode('股骨头球心')
  #     # self.ShowNode('H点')
  #     #显示股骨并将股骨透明化
  #     Femur = slicer.util.getNode('Femur')
  #     Femur.SetDisplayVisibility(1)
  #     Femur.GetDisplayNode().SetOpacity(0.2)
  #     # 回到骨骼参数
  #     self.ui.Parameter.click()

  #   elif c == qt.QMessageBox.Cancel:
  #     self.ui.Reset.setChecked(False)
  #     self.ui.Reset2.setChecked(False)
  #----------------------------------------------------------------------------
  #显示力线
  def onForceLine(self):

    # self.FemurButtonChecked(self.ui.ForceLine)
    # self.TibiaButtonChecked(self.ui.ForceLine2)
    
    try:
      slicer.mrmlScene.RemoveNode(slicer.util.getNode('OutSide'))
      slicer.mrmlScene.RemoveNode(slicer.util.getNode('InSide'))
    except:
      pass
    # self.HideAll()
    # self.ui.Graph.show()
    # self.ui.ForceWidget.setVisible(True)

    # slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutTriple3DEndoscopyView)#将 view1,view2,view3添加到场景中
    # self.ThreeDState()#三维视图状态正常
    # self.hideInformation()
    self.DrawLine()
    # slicer.app.layoutManager().threeDWidget('View1').installEventFilter(self.resizeEvent)
    # slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutSideBySideView)
    # self.ThreeDViewAndImageWidget(2)
    ras1, ras2, ras3, ras4 = [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]
    slicer.util.getNode('股骨头球心').GetNthFiducialPosition(0, ras1)
    slicer.util.getNode('开髓点').GetNthFiducialPosition(0, ras2)
    slicer.util.getNode('外侧凸点').GetNthFiducialPosition(0, ras3)
    slicer.util.getNode('内侧凹点').GetNthFiducialPosition(0, ras4)
    zb1 = [-ras1[0], -ras1[1], ras1[2]]  # 坐标1，球心
    zb2 = [-ras2[0], -ras2[1], ras2[2]]  # 坐标2，原点
    zb3 = [-ras3[0], -ras3[1], ras3[2]]  # 坐标3，左侧点
    zb4 = [-ras4[0], -ras4[1], ras4[2]]  # 坐标4，右侧点
    jxlz = [0, 0, 0]  # Y轴基向量
    for i in range(0, 3):
        jxlz[i] = zb1[i] - zb2[i]
    moz = np.sqrt(np.square(jxlz[0]) + np.square(jxlz[1]) + np.square(jxlz[2]))  # 基向量z的模
    for i in range(0, 3):
        jxlz[i] = jxlz[i] / moz
    csD = jxlz[0] * zb2[0] + jxlz[1] * zb2[1] + jxlz[2] * zb2[2]  # 平面方程参数D
    csT3 = (jxlz[0] * zb3[0] + jxlz[1] * zb3[1] + jxlz[2] * zb3[2] - csD) / (
            jxlz[0] * jxlz[0] + jxlz[1] * jxlz[1] + jxlz[2] * jxlz[2])  # 坐标3平面方程参数T
    ty3 = [0, 0, 0]  # 坐标3在YZ平面的投影
    for i in range(0, 3):
        ty3[i] = zb3[i] - jxlz[i] * csT3
    csT4 = (jxlz[0] * zb4[0] + jxlz[1] * zb4[1] + jxlz[2] * zb4[2] - csD) / (
            jxlz[0] * jxlz[0] + jxlz[1] * jxlz[1] + jxlz[2] * jxlz[2])
    ty4 = [0, 0, 0]
    for i in range(0, 3):
        ty4[i] = zb4[i] - jxlz[i] * csT4
    jxlx = [0, 0, 0]  # X轴基向量
    for i in range(0, 3):
        if slicer.modules.NoImageWelcomeWidget.judge == 'L':
            jxlx[i] = ty3[i] - ty4[i]
        else:
            jxlx[i] = ty4[i] - ty3[i]
    mox = np.sqrt(np.square(jxlx[0]) + np.square(jxlx[1]) + np.square(jxlx[2]))  # 基向量X的模
    for i in range(0, 3):
        jxlx[i] = jxlx[i] / mox
    jxly = [0, 0, 0]  # y轴基向量
    jxly[0] = -(jxlx[1] * jxlz[2] - jxlx[2] * jxlz[1])
    jxly[1] = -(jxlx[2] * jxlz[0] - jxlx[0] * jxlz[2])
    jxly[2] = -(jxlx[0] * jxlz[1] - jxlx[1] * jxlz[0])
    moy = np.sqrt(np.square(jxly[0]) + np.square(jxly[1]) + np.square(jxly[2]))  # 基向量y的模
    for i in range(0, 3):
        jxly[i] = jxly[i] / moy
    ccb = ([jxlx, jxly, jxlz])
    ccc = np.asarray(ccb)
    ccd = ccc.T
    np.savetxt(self.FilePath + "/Femur-jxl.txt", ccd, fmt='%6f')
    Ftrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    self.Ftrans2 = np.array([[float(jxlx[0]), float(jxly[0]), float(jxlz[0]), zb2[0]],
                            [float(jxlx[1]), float(jxly[1]), float(jxlz[1]), zb2[1]],
                            [float(jxlx[2]), float(jxly[2]), float(jxlz[2]), zb2[2]],
                            [0, 0, 0, 1]])
    self.FemurForceTrans = np.dot(Ftrans1,self.Ftrans2)
    
    ras1, ras2, ras3= [0, 0, 0], [0, 0, 0], [0, 0, 0]
    slicer.util.getNode('胫骨隆凸').GetNthFiducialPosition(0, ras1)
    slicer.util.getNode('胫骨结节').GetNthFiducialPosition(0, ras2)
    slicer.util.getNode('踝穴中心').GetNthFiducialPosition(0, ras3)

    Tzb1 = [-ras1[0], -ras1[1], ras1[2]]  # 坐标1，原点，髌骨近端的点
    Tzb2 = [-ras2[0], -ras2[1], ras2[2]]  # 坐标2，髌骨中间的点
    Tzb3 = [-ras3[0], -ras3[1], ras3[2]]  # 坐标2，髌骨远端的点
    Tjxlz = [0, 0, 0]  # z轴基向量
    for i in range(0, 3):
        Tjxlz[i] = Tzb1[i] - Tzb3[i]
    moz = np.sqrt(np.square(Tjxlz[0]) + np.square(Tjxlz[1]) + np.square(Tjxlz[2]))  # 基向量z的模
    for i in range(0, 3):
        Tjxlz[i] = Tjxlz[i] / moz
    TcsD = Tjxlz[0] * Tzb1[0] + Tjxlz[1] * Tzb1[1] + Tjxlz[2] * Tzb1[2]  # 平面方程参数D
    TcsT2 = (Tjxlz[0] * Tzb2[0] + Tjxlz[1] * Tzb2[1] + Tjxlz[2] * Tzb2[2] - TcsD) / (
            Tjxlz[0] * Tjxlz[0] + Tjxlz[1] * Tjxlz[1] + Tjxlz[2] * Tjxlz[2])  # 坐标3平面方程参数T
    Tty2 = [0, 0, 0]  # 坐标2在XY平面的投影
    for i in range(0, 3):
        Tty2[i] = Tzb2[i] - Tjxlz[i] * TcsT2
    Tjxly = [0, 0, 0]  # y轴基向量
    for i in range(0, 3):
        Tjxly[i] = Tzb1[i] - Tty2[i]
    moy = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量y的模
    for i in range(0, 3):
        Tjxly[i] = Tjxly[i] / moy
    Tjxlx = [0, 0, 0]  # x轴基向量
    Tjxlx[0] = -(Tjxlz[1] * Tjxly[2] - Tjxlz[2] * Tjxly[1])
    Tjxlx[1] = -(Tjxlz[2] * Tjxly[0] - Tjxlz[0] * Tjxly[2])
    Tjxlx[2] = -(Tjxlz[0] * Tjxly[1] - Tjxlz[1] * Tjxly[0])
    mox = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量x的模
    for i in range(0, 3):
        Tjxlx[i] = Tjxlx[i] / mox
    Tzb3xz = []
    jd = 1
    jd = math.radians(jd)
    zhjz = np.array([[Tjxlx[0], Tjxly[0], Tjxlz[0], Tzb1[0]], [Tjxlx[1], Tjxly[1], Tjxlz[1], Tzb1[1]],
            [Tjxlx[2], Tjxly[2], Tjxlz[2], Tzb1[2]], [0, 0, 0, 1]])
    Tzb3xz3 = self.GetMarix(zhjz,1,Tzb3)
    # for i in range(0, 3):
    #     Tzb3[i] = Tzb3xz3[i]
    Tjxlz = [0, 0, 0]  # z轴基向量
    for i in range(0, 3):
        Tjxlz[i] = Tzb1[i] - Tzb3[i]
    moz = np.sqrt(np.square(Tjxlz[0]) + np.square(Tjxlz[1]) + np.square(Tjxlz[2]))  # 基向量z的模
    for i in range(0, 3):
        Tjxlz[i] = Tjxlz[i] / moz
    TcsD = Tjxlz[0] * Tzb1[0] + Tjxlz[1] * Tzb1[1] + Tjxlz[2] * Tzb1[2]  # 平面方程参数D
    TcsT2 = (Tjxlz[0] * Tzb2[0] + Tjxlz[1] * Tzb2[1] + Tjxlz[2] * Tzb2[2] - TcsD) / (
            Tjxlz[0] * Tjxlz[0] + Tjxlz[1] * Tjxlz[1] + Tjxlz[2] * Tjxlz[2])  # 坐标3平面方程参数T
    Tty2 = [0, 0, 0]  # 坐标2在XY平面的投影
    for i in range(0, 3):
        Tty2[i] = Tzb2[i] - Tjxlz[i] * TcsT2
    Tjxly = [0, 0, 0]  # y轴基向量
    for i in range(0, 3):
        Tjxly[i] = Tzb1[i] - Tty2[i]
    moy = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量y的模
    for i in range(0, 3):
        Tjxly[i] = Tjxly[i] / moy
    Tjxlx = [0, 0, 0]  # X轴基向量
    Tjxlx[0] = -(Tjxlz[1] * Tjxly[2] - Tjxlz[2] * Tjxly[1])
    Tjxlx[1] = -(Tjxlz[2] * Tjxly[0] - Tjxlz[0] * Tjxly[2])
    Tjxlx[2] = -(Tjxlz[0] * Tjxly[1] - Tjxlz[1] * Tjxly[0])
    mox = np.sqrt(np.square(Tjxlx[0]) + np.square(Tjxlx[1]) + np.square(Tjxlx[2]))  # 基向量x的模
    for i in range(0, 3):
        Tjxlx[i] = Tjxlx[i] / mox
    ccb = ([Tjxlx, Tjxly, Tjxlz])
    ccc = np.asarray(ccb)
    ccd = ccc.T
    np.savetxt(self.FilePath + "/Tibia-jxl.txt", ccd, fmt='%6f')
    Ttrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    Ttrans2 = np.array([[float(Tjxlx[0]), float(Tjxly[0]), float(Tjxlz[0]), Tzb1[0]],
                            [float(Tjxlx[1]), float(Tjxly[1]), float(Tjxlz[1]), Tzb1[1]],
                            [float(Tjxlx[2]), float(Tjxly[2]), float(Tjxlz[2]), Tzb1[2]],
                            [0, 0, 0, 1]])
    self.TibiaForceTrans = np.dot(Ttrans1,Ttrans2)

    # self.ForceLineImage()

    # self.interactorStyle1.SetInteractor(None)
    # self.interactorStyle2.SetInteractor(None)
    rotationTransformNode = slicer.util.getNode('DianjiToTracker1')
    try:
      rotationTransformNode.RemoveObserver(self.ZuiDiDian)
    except:
      pass
    self.updataForceAngle = rotationTransformNode.AddObserver(
      slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.updataAngle)
    # self.ForceCamera1(self.view1)
    # self.ForceCamera2(self.view2)
    # self.view1.resetFocalPoint()
    # self.view2.resetFocalPoint()

  
  def ForceLineImage(self):

    #self = slicer.modules.noimage.widgetRepresentation().self()
    # self.ui.GraphImage.setAutoFillBackground(True)
    # viewLayout = qt.QVBoxLayout()
    # self.ui.GraphImage.setLayout(viewLayout)
    pg.setConfigOption('background', '#454647')
    self.win = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
    # layout = shiboken2.wrapInstance(hash(viewLayout),QVBoxLayout)
    # layout.addWidget(self.win)
    pg.setConfigOptions(antialias=True)


    self.p1 = self.win.addPlot()
    self.p1.showGrid(True,True,0.1)
    line = self.p1.plot([0,0],[0,0],pen='#7cbd27')

    self.lineList=[]
    for i in range(141):
      self.lineList.append(0)
    self.lineList2=[]
    for i in range(141):
      self.lineList2.append(0)

    
    #显示图例
    legend3 = pg.LegendItem((20,5), offset=(10,27))
    legend3.setParentItem(self.p1)
    legend3.addItem(line, '角度(°)')
    ticks1 = [-20,-10,-3,0,3,10,20]
    ticks = [-10,0,10,20,30,40,50,60,70,80,90,100,110,120,130]
    #Y轴
    ay = self.p1.getAxis('left')
    ay.setTicks([[(v, str(v)) for v in ticks ]])
    #X轴
    ax = self.p1.getAxis('bottom')   
    ax.setTicks([[(v, str(v)) for v in ticks1 ]])  

  def ForceCamera1(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([0, -1500, 0, 1])
    Ftrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('DianjiToTracker1')
    Ftrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ftrans1=np.dot(Ftrans_dj,Ftrans1)
    Ftrans3 = np.dot(Ftrans1, self.Ftrans2)
    position1 = np.dot(Ftrans3, positiontmp)
    viewUpDirection = (float(Ftrans3[0][2]), float(Ftrans3[1][2]), float(Ftrans3[2][2]))
    focalPoint1 = [Ftrans3[0][3], Ftrans3[1][3], Ftrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint1)
    cameraNode.SetPosition(position1[0], position1[1], position1[2])
    cameraNode.SetViewUp(viewUpDirection)
    cameraNode.SetAndObserveTransformNodeID(transNode.GetID())


  def ForceCamera2(self, view):
    cameraNode = view.cameraNode()
    positiontmp = np.array([-1500, 0, 0, 1])
    Ftrans1 = np.array([[-1, 0, 0, 0],
                        [0, -1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    transNode = slicer.util.getNode('DianjiToTracker1')
    Ftrans_dj = slicer.util.arrayFromTransformMatrix(transNode)
    Ftrans1 = np.dot(Ftrans_dj, Ftrans1)
    Ftrans3 = np.dot(Ftrans1, self.Ftrans2)
    position2 = np.dot(Ftrans3, positiontmp)
    viewUpDirection = (float(Ftrans3[0][2]), float(Ftrans3[1][2]), float(Ftrans3[2][2]))
    focalPoint2 = [Ftrans3[0][3], Ftrans3[1][3], Ftrans3[2][3]]
    cameraNode.SetFocalPoint(focalPoint2)
    cameraNode.SetPosition(position2[0], position2[1], position2[2])
    cameraNode.SetViewUp(viewUpDirection)
    cameraNode.SetAndObserveTransformNodeID(transNode.GetID())

  
  def onForceConfirm(self):
    angle = 0
    self.ui.ForceAngle.setText('力线角度：'+str(angle))
  
  #画外翻角角度
  def DrawLine(self):
    try:
      slicer.mrmlScene.RemoveNode(slicer.util.getNode("FemurLine"))
      slicer.mrmlScene.RemoveNode(slicer.util.getNode("TibiaLine"))      
    except:
      pass

    ras1,ras2,ras3,ras4 = [0,0,0],[0,0,0],[0,0,0],[0,0,0]
    slicer.util.getNode('股骨头球心').GetNthControlPointPositionWorld(0, ras1)
    slicer.util.getNode('开髓点').GetNthControlPointPositionWorld(0, ras2)
    slicer.util.getNode('胫骨隆凸').GetNthControlPointPositionWorld(0, ras3)
    slicer.util.getNode('踝穴中心').GetNthControlPointPositionWorld(0, ras4)
    ras5 = [ras2[0]+ras4[0]-ras3[0],ras2[1]+ras4[1]-ras3[1],ras2[2]+ras4[2]-ras3[2]]
    FemurLine = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode','FemurLine')
    FemurLine.AddControlPoint(ras1)
    FemurLine.AddControlPoint(ras2)
    FemurLine.GetDisplayNode().SetPropertiesLabelVisibility(0)
    FemurLine.GetDisplayNode().SetGlyphScale(2) 
    FemurLine.GetDisplayNode().SetSelectedColor(0.48627450980392156, 0.7411764705882353, 0.15294117647058825)
    FemurLine.SetNthControlPointLocked(0,True)
    FemurLine.SetNthControlPointLocked(1,True)
    TibiaLine = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode','TibiaLine')
    TibiaLine.AddControlPoint(ras3)
    TibiaLine.AddControlPoint(ras4)
    TibiaLine.GetDisplayNode().SetPropertiesLabelVisibility(0)
    TibiaLine.GetDisplayNode().SetGlyphScale(2) 
    TibiaLine.GetDisplayNode().SetSelectedColor(0.48627450980392156, 0.7411764705882353, 0.15294117647058825)
    TibiaLine.SetNthControlPointLocked(0,True)
    TibiaLine.SetNthControlPointLocked(1,True)
    # WaiFanJiao = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsAngleNode','Angle')
    # WaiFanJiao.AddControlPoint(ras1)
    # WaiFanJiao.AddControlPoint(ras2)
    # WaiFanJiao.AddControlPoint(ras5)
    # WaiFanJiao.GetDisplayNode().SetTextScale(3)
    # WaiFanJiao.SetNthControlPointLocked(0,True)
    # WaiFanJiao.SetNthControlPointLocked(1,True)
    # WaiFanJiao.SetNthControlPointLocked(2,True)
    xiangliang1 = [ras1[0]-ras2[0],ras1[1]-ras2[1],ras1[2]-ras2[2]]
    xiangliang2 = [ras4[0]-ras3[0],ras4[1]-ras3[1],ras4[2]-ras3[2]]
    angle = self.Angle(xiangliang1,xiangliang2)
    print(angle)
    # self.ForceLabel1 = qt.QLabel(self.view1)
    # self.ForceLabel2 = qt.QLabel(self.view2)
    # self.ForceLabel1.setGeometry(self.view1.contentsRect().width()/2, 25, 200, 40)
    # self.ForceLabel1.setText("外翻角度："+str(round(angle,2))+'°')
    # self.ForceLabel1.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    # self.ForceLabel1.show()
    # self.ForceLabel2.setGeometry(self.view2.contentsRect().width()/2, 25, 200, 40)
    # self.ForceLabel2.setText("屈膝角度："+str(round(angle,2))+'°')
    # self.ForceLabel2.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
    # self.ForceLabel2.show()
  
  #实时更新角度
  def updataAngle(self,unusedArg1=None, unusedArg2=None, unusedArg3=None):

    ras1,ras2,ras3,ras4 = [0,0,0],[0,0,0],[0,0,0],[0,0,0]
    slicer.util.getNode('股骨头球心').GetNthControlPointPositionWorld(0, ras1)
    slicer.util.getNode('开髓点').GetNthControlPointPositionWorld(0, ras2)
    slicer.util.getNode('胫骨隆凸').GetNthControlPointPositionWorld(0, ras3)
    slicer.util.getNode('踝穴中心').GetNthControlPointPositionWorld(0, ras4)
    #更新画的两条线
    try:
      FemurLine = slicer.util.getNode('FemurLine')
      TibiaLine = slicer.util.getNode('TibiaLine')
      FemurLine.SetNthControlPointPosition(0,ras1)
      FemurLine.SetNthControlPointPosition(1,ras2)
      TibiaLine.SetNthControlPointPosition(0,ras3)
      TibiaLine.SetNthControlPointPosition(1,ras4)
    except:
      print("FemurLine已删除")

    #更新角度
    transNode=slicer.util.getNode('DianjiToTracker1')
    trans_dj=slicer.util.arrayFromTransformMatrix(transNode)
    TibiaNode = slicer.util.getNode('TibiaToTracker')
    trans_Tibia=slicer.util.arrayFromTransformMatrix(TibiaNode)
    Femurtans = np.dot(trans_dj,self.FemurForceTrans)
    Tibiatrans = np.dot(trans_Tibia,self.TibiaForceTrans)
    FemurPoint = np.array([[0.0, 0.0, 0.0, 1.0], [100.0, 0.0, 0.0, 1.0], [0.0, 100.0, 0.0, 1.0], [0.0, 0.0, 100.0, 1.0]])
    TibiaPoint = np.array([[0.0, 0.0, 0.0, 1.0], [100.0, 0.0, 0.0, 1.0], [0.0, 100.0, 0.0, 1.0], [0.0, 0.0, 100.0, 1.0]])
    for i in range(4):
      FemurPoint[i]=np.dot(Femurtans,FemurPoint[i])
    for i in range(4):
      TibiaPoint[i]=np.dot(Tibiatrans,TibiaPoint[i])
    Tibia_YZPlane=TibiaPoint[[0,2,3],0:3]
    Tibia_XZPlane = TibiaPoint[[0,1,3],0:3]
    Femur_Z = self.TouYing(Tibia_YZPlane,FemurPoint[3][0:3])
    Femur_L = self.TouYing(Tibia_YZPlane,FemurPoint[0][0:3])
    Femur_ZAxis_Z = np.array(Femur_Z)-np.array(Femur_L)

    Femur_Z1 = self.TouYing(Tibia_XZPlane,FemurPoint[1][0:3])
    Femur_L1 = self.TouYing(Tibia_XZPlane,FemurPoint[0][0:3])
    Femur_XAxis_Z = np.array(Femur_Z1)-np.array(Femur_L1)

    Tibia_XAxis = (TibiaPoint[1]-TibiaPoint[0])[0:3]
    Tibia_YAxis = (TibiaPoint[2]-TibiaPoint[0])[0:3]
    Tibia_ZAxis = (TibiaPoint[3]-TibiaPoint[0])[0:3]

    quxiAngle = self.Angle(Femur_ZAxis_Z,Tibia_ZAxis)
    
    Ifzf1 = np.dot(Femur_ZAxis_Z,Tibia_YAxis)
    Ifzf2 = np.dot(Femur_XAxis_Z,Tibia_ZAxis)
    if Ifzf2 < 0:
      waifanAngle = -float(self.angle(Femur_XAxis_Z, Tibia_XAxis))
    else:
      waifanAngle = float(self.angle(Femur_XAxis_Z, Tibia_XAxis))
    if Ifzf1<0:
      quxiAngle = -quxiAngle
    
    self.ForceLabel1.setText('外翻角度：'+str(round(waifanAngle,1))+'°')
    self.ForceLabel2.setText('屈膝角度：'+str(round(quxiAngle,1))+'°')
    #更新图
    if Ifzf1<0:
      if Ifzf2>0:#屈膝角度是负值，外翻角度是正值
        if self.lineList[10-int(float(quxiAngle))]==0 and (10-int(float(quxiAngle)))%2 == 0:
          line=self.p1.plot([0,waifanAngle],[-int(quxiAngle),-int(quxiAngle)],pen=pg.mkPen('#7cbd27',width=5))
          self.lineList[10-int(float(quxiAngle))]=line
        elif self.lineList[10-int(float(quxiAngle))]!=0 and (10-int(float(quxiAngle)))%2 == 0:
          a = self.lineList[10-int(float(quxiAngle))].getData()
          if waifanAngle>a[0][1]:
            self.lineList[10-int(float(quxiAngle))].setData([0,waifanAngle],[-int(quxiAngle),-int(quxiAngle)])
      else:#屈膝角度是负值，外翻角度是负值
        if self.lineList2[10-int(float(quxiAngle))]==0 and (10-int(float(quxiAngle)))%2 == 0:#画线区间为2
          line=self.p1.plot([0,waifanAngle],[-int(quxiAngle),-int(quxiAngle)],pen=pg.mkPen('#7cbd27',width=5))
          self.lineList2[10-int(float(quxiAngle))]=line
        elif self.lineList2[10-int(float(quxiAngle))]!=0 and (10-int(float(quxiAngle)))%2 == 0:
          a = self.lineList2[10-int(float(quxiAngle))].getData()
          if waifanAngle<a[0][1]:
            self.lineList2[10-int(float(quxiAngle))].setData([0,waifanAngle],[-int(quxiAngle),-int(quxiAngle)])
    else:
      if Ifzf2>0:#屈膝角度是正值，外翻角度是正值
        if self.lineList[int(float(quxiAngle))-1]==0 and (int(float(quxiAngle))-1)%2 == 0:
          line=self.p1.plot([0,waifanAngle],[int(quxiAngle),int(quxiAngle)],pen=pg.mkPen('#7cbd27',width=5))
          self.lineList[int(float(quxiAngle))-1]=line
        elif self.lineList[int(float(quxiAngle))-1]!=0 and (int(float(quxiAngle))-1)%2 == 0:
          a = self.lineList[int(float(quxiAngle))-1].getData()
          if waifanAngle>a[0][1]:
            self.lineList[int(float(quxiAngle))-1].setData([0,waifanAngle],[int(quxiAngle),int(quxiAngle)])
      else:#屈膝角度是正值，外翻角度是负值
        if self.lineList2[int(float(quxiAngle))-1]==0 and (int(float(quxiAngle))-1)%2 == 0:
          line=self.p1.plot([0,waifanAngle],[int(quxiAngle),int(quxiAngle)],pen=pg.mkPen('#7cbd27',width=5))
          self.lineList2[int(float(quxiAngle))-1]=line
        elif self.lineList2[int(float(quxiAngle))-1]!=0 and (int(float(quxiAngle))-1)%2 == 0:
          a = self.lineList2[int(float(quxiAngle))-1].getData()
          if waifanAngle<a[0][1]:
            self.lineList2[int(float(quxiAngle))-1].setData([0,waifanAngle],[int(quxiAngle),int(quxiAngle)])
    
    # self.ForceCamera1(self.view1)
    # self.ForceCamera2(self.view2)
    self.currentX=quxiAngle
    self.currentY=waifanAngle

    #膝关节评估动态UI
    self.leg_rotation.setRotation(self.currentX)#腿旋转
    self.flipcorner.OnhhhMoved(self.currentX)#内外翻滑杆上下移动
    self.flipcorner.OnvvvMoved(self.currentY)#内外翻滑杆左右移动



  #------------------------胫骨-----------------------------------------------
  #胫骨骨骼参数
  def onParameter2(self):
    #self.HideAll()
    # self.ui.OperationPlanWidget.setVisible(True)
    # self.ui.GuGe.setVisible(True)
    ROIs = slicer.util.getNodesByClass('vtkMRMLMarkupsROINode')
    models = slicer.util.getNodesByClass('vtkMRMLModelNode')

    

    Name = []
    for i in range(0, len(models)):
      a = models[i]
      Name.append(a.GetName())
    if '胫骨近端' in Name:
      self.HidePart()
      self.ShowNode('胫骨近端')
    else:
      if len(ROIs) < 9:
        Tibia1 = slicer.util.getNode('Tibia')
        Tibia1.GetDisplayNode().SetOpacity(1)
        ras1, ras2, ras3= [0, 0, 0], [0, 0, 0], [0, 0, 0]
        slicer.util.getNode('胫骨隆凸').GetNthFiducialPosition(0, ras1)
        slicer.util.getNode('胫骨结节').GetNthFiducialPosition(0, ras2)
        slicer.util.getNode('踝穴中心').GetNthFiducialPosition(0, ras3)
        Tzb1 = [ras1[0], ras1[1], ras1[2]]  # 坐标1，原点，髌骨近端的点
        Tzb2 = [ras2[0], ras2[1], ras2[2]]  # 坐标2，髌骨中间的点
        Tzb3 = [ras3[0], ras3[1], ras3[2]]  # 坐标2，髌骨远端的点
        Tjxlz = [0, 0, 0]  # z轴基向量
        for i in range(0, 3):
            Tjxlz[i] = Tzb1[i] - Tzb3[i]
        moz = np.sqrt(np.square(Tjxlz[0]) + np.square(Tjxlz[1]) + np.square(Tjxlz[2]))  # 基向量z的模
        for i in range(0, 3):
            Tjxlz[i] = Tjxlz[i] / moz
        TcsD = Tjxlz[0] * Tzb1[0] + Tjxlz[1] * Tzb1[1] + Tjxlz[2] * Tzb1[2]  # 平面方程参数D
        TcsT2 = (Tjxlz[0] * Tzb2[0] + Tjxlz[1] * Tzb2[1] + Tjxlz[2] * Tzb2[2] - TcsD) / (
                Tjxlz[0] * Tjxlz[0] + Tjxlz[1] * Tjxlz[1] + Tjxlz[2] * Tjxlz[2])  # 坐标3平面方程参数T
        Tty2 = [0, 0, 0]  # 坐标2在XY平面的投影
        for i in range(0, 3):
            Tty2[i] = Tzb2[i] - Tjxlz[i] * TcsT2
        Tjxly = [0, 0, 0]  # y轴基向量
        for i in range(0, 3):
            Tjxly[i] = Tzb1[i] - Tty2[i]
        moy = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量y的模
        for i in range(0, 3):
            Tjxly[i] = Tjxly[i] / moy
        Tjxlx = [0, 0, 0]  # x轴基向量
        Tjxlx[0] = (Tjxlz[1] * Tjxly[2] - Tjxlz[2] * Tjxly[1])
        Tjxlx[1] = (Tjxlz[2] * Tjxly[0] - Tjxlz[0] * Tjxly[2])
        Tjxlx[2] = (Tjxlz[0] * Tjxly[1] - Tjxlz[1] * Tjxly[0])
        mox = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量x的模
        for i in range(0, 3):
            Tjxlx[i] = Tjxlx[i] / mox
        Tzb3xz = []
        jd = 1
        jd = math.radians(jd)
        zhjz = np.array([[Tjxlx[0], Tjxly[0], Tjxlz[0], Tzb1[0]], [Tjxlx[1], Tjxly[1], Tjxlz[1], Tzb1[1]],
                [Tjxlx[2], Tjxly[2], Tjxlz[2], Tzb1[2]], [0, 0, 0, 1]])
        Tzb3xz3 = self.GetMarix(zhjz,1,Tzb3)
        # for i in range(0, 3):
        #     Tzb3[i] = Tzb3xz3[i]
        Tjxlz = [0, 0, 0]  # z轴基向量
        for i in range(0, 3):
            Tjxlz[i] = Tzb1[i] - Tzb3[i]
        moz = np.sqrt(np.square(Tjxlz[0]) + np.square(Tjxlz[1]) + np.square(Tjxlz[2]))  # 基向量z的模
        for i in range(0, 3):
            Tjxlz[i] = Tjxlz[i] / moz
        TcsD = Tjxlz[0] * Tzb1[0] + Tjxlz[1] * Tzb1[1] + Tjxlz[2] * Tzb1[2]  # 平面方程参数D
        TcsT2 = (Tjxlz[0] * Tzb2[0] + Tjxlz[1] * Tzb2[1] + Tjxlz[2] * Tzb2[2] - TcsD) / (
                Tjxlz[0] * Tjxlz[0] + Tjxlz[1] * Tjxlz[1] + Tjxlz[2] * Tjxlz[2])  # 坐标3平面方程参数T
        Tty2 = [0, 0, 0]  # 坐标2在XY平面的投影
        for i in range(0, 3):
            Tty2[i] = Tzb2[i] - Tjxlz[i] * TcsT2
        Tjxly = [0, 0, 0]  # y轴基向量
        for i in range(0, 3):
            Tjxly[i] = Tty2[i]-Tzb1[i]
        moy = np.sqrt(np.square(Tjxly[0]) + np.square(Tjxly[1]) + np.square(Tjxly[2]))  # 基向量y的模
        for i in range(0, 3):
            Tjxly[i] = Tjxly[i] / moy
        Tjxlx = [0, 0, 0]  # X轴基向量
        Tjxlx[0] = (Tjxlz[1] * Tjxly[2] - Tjxlz[2] * Tjxly[1])
        Tjxlx[1] = (Tjxlz[2] * Tjxly[0] - Tjxlz[0] * Tjxly[2])
        Tjxlx[2] = (Tjxlz[0] * Tjxly[1] - Tjxlz[1] * Tjxly[0])
        mox = np.sqrt(np.square(Tjxlx[0]) + np.square(Tjxlx[1]) + np.square(Tjxlx[2]))  # 基向量x的模
        for i in range(0, 3):
            Tjxlx[i] = Tjxlx[i] / mox
        ccb = ([Tjxlx, Tjxly, Tjxlz])
        ccc = np.asarray(ccb)
        ccd = ccc.T
        #np.savetxt(self.FilePath + "/Tibia-jxl.txt", ccd, fmt='%6f')
        Ttrans1 = np.array([[-1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])
        Ttrans2 = np.array([[float(Tjxlx[0]), float(Tjxly[0]), float(Tjxlz[0]), Tzb1[0]],
                                [float(Tjxlx[1]), float(Tjxly[1]), float(Tjxlz[1]), Tzb1[1]],
                                [float(Tjxlx[2]), float(Tjxly[2]), float(Tjxlz[2]), Tzb1[2]],
                                [0, 0, 0, 1]])
        self.Ttrans3=np.dot(Ttrans1,np.linalg.inv(Ttrans2))
        Ttrans4 = np.array([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])
        Ttransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_胫骨临时')
        Ttransform1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_胫骨约束')
        Ttransform2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_胫骨调整')
        Ttransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(self.Ttrans3))
        Ttransform1.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ttrans4))
        Ttransform2.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(Ttrans4))
        Ttransform2.SetAndObserveTransformNodeID(Ttransform1.GetID())
        inputModel = slicer.util.getNode('Tibia')
        inputModel.SetAndObserveTransformNodeID(Ttransform.GetID())
        inputModel.HardenTransform()
        #将所有点复制出一份放到截骨调整中
        TibiaPoints = ['胫骨隆凸','胫骨结节','外侧高点','内侧高点','踝穴中心']
        for i in range(len(TibiaPoints)):
            PointNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', TibiaPoints[i]+"1")
            point = [0, 0, 0]
            node1=slicer.util.getNode(TibiaPoints[i]).GetNthControlPointPosition(0, point)
            point=[point[0],point[1],point[2],1]
            PointNode.AddControlPoint(np.dot(self.Ttrans3,point)[0:3])
            PointNode.SetAndObserveTransformNodeID(Ttransform2.GetID())
        roiNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsROINode', '胫骨近端切割')
        roiNode.SetCenter([0, 0, 0])
        roiNode.SetSize([100, 100, 140])
        roiNode.SetDisplayVisibility(False)
        TibiaJinDuan = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", "胫骨近端")
        inputModel = slicer.util.getNode('Tibia')
        inputROI = roiNode
        dynamicModelerNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLDynamicModelerNode")
        dynamicModelerNode.SetToolName("ROI cut")
        dynamicModelerNode.SetNodeReferenceID("ROICut.InputModel", inputModel.GetID())
        dynamicModelerNode.SetNodeReferenceID("ROICut.InputROI", inputROI.GetID())
        dynamicModelerNode.SetNodeReferenceID("ROICut.OutputPositiveModel", TibiaJinDuan.GetID())
        # dynamicModelerNode.SetContinuousUpdate(1)
        dynamicModelerNode.SetAttribute("ROICut.CapSurface", '1')
        slicer.modules.dynamicmodeler.logic().RunDynamicModelerTool(dynamicModelerNode)
        inputModel.SetDisplayVisibility(False)
        slicer.util.getNode('Tibia').SetDisplayVisibility(False)
    



        #self.addAxisTibia()#添加假体及骨骼的坐标轴
        self.SelectTibiaJiaTi()
        self.onTibiaJiaTi(1)
        #self.TibiaJiaTiload.SetAndObserveTransformNodeID(Ttransform3.GetID())
        #self.TibiaJiaTiload.SetDisplayVisibility(False)

        self.NodeMove('胫骨近端', '变换_胫骨调整')
        #添加至新的坐标系中，以计算外翻角
        o = [0, 0, 0]
        z = [0, 0, 1]
        y = [0, 1, 0]
        x = [1, 0, 0]
        f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Femur_ZAxis1')
        f.AddControlPoint(o)
        f.AddControlPoint(z)
        Femur_ZAxis = slicer.util.getNode('变换_股骨调整')
        f.SetAndObserveTransformNodeID(Femur_ZAxis.GetID())
        f.SetDisplayVisibility(False)


        f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Femur_XAxis1')
        f.AddControlPoint(o)
        f.AddControlPoint(z)
        Femur_ZAxis = slicer.util.getNode('变换_股骨调整')
        f.SetAndObserveTransformNodeID(Femur_ZAxis.GetID())
        f.SetDisplayVisibility(False)

        f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_ZAxis1')
        f.AddControlPoint(o)
        f.AddControlPoint(z)
        Tibia_ZAxis = slicer.util.getNode('变换_胫骨调整')
        f.SetAndObserveTransformNodeID(Tibia_ZAxis.GetID())
        f.SetDisplayVisibility(False)

        f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_XAxis1')
        f.AddControlPoint(o)
        f.AddControlPoint(x)
        Tibia_XAxis = slicer.util.getNode('变换_胫骨调整')
        f.SetAndObserveTransformNodeID(Tibia_XAxis.GetID())
        f.SetDisplayVisibility(False)

        f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_YAxis1')
        f.AddControlPoint(o)
        f.AddControlPoint(y)
        Tibia_YAxis = slicer.util.getNode('变换_胫骨调整')
        f.SetAndObserveTransformNodeID(Tibia_YAxis.GetID())
        f.SetDisplayVisibility(False)

        f = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'Tibia_YZPlane1')
        f.AddControlPoint(o)
        f.AddControlPoint(y)
        f.AddControlPoint(z)
        Tibia_YZPlane = slicer.util.getNode('变换_胫骨调整')
        f.SetAndObserveTransformNodeID(Tibia_YZPlane.GetID())
        f.SetDisplayVisibility(False)


    # self.TCamera1(self.view1)
    # self.TCamera2(self.view2)
    # self.TCamera3(self.view3)
    #self.ui.ModuleName.setText('手术规划')
  
  #确定胫骨截骨面，并正确放置假体位置     
  def TibiaJieGu(self):
    # 胫骨截骨面
    TibiaJieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '胫骨截骨面')
    TibiaJieGu.AddControlPoint(30, 0, 0)
    TibiaJieGu.AddControlPoint(0, 30, 0)
    TibiaJieGu.AddControlPoint(0, 0, 0)
    TtransformYueShu = slicer.util.getNode('变换_胫骨约束')
    #TibiaJieGu.SetAndObserveTransformNodeID(TtransformYueShu.GetID())
    point = [0, 0, 0]
    point1 = [0, 0, 0]
    point3 = [0, 0, 0]
    slicer.util.getNode('内侧高点1').GetNthControlPointPositionWorld(0, point)
    slicer.util.getNode('外侧高点1').GetNthControlPointPositionWorld(0, point1)
    slicer.util.getNode('胫骨隆凸1').GetNthControlPointPositionWorld(0, point3)
    self.HideNode('胫骨截骨面')
    TibiaJGM = self.GetTransPoint('胫骨截骨面')
    pointTouYing = np.array(self.TouYing(TibiaJGM,point))



    xiangliang=(point-pointTouYing)[0:3]
    z=[0,0,1]
    x=np.dot(xiangliang,z)

    print('x',x)
    d = self.point2area_distance(TibiaJGM, point)
    print('d:',d)
    if x > 0:
      d = -d
    distance = 6 + d

    
    


    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      angle_point=(np.array(point1)-point)[0:2]
    else:
      angle_point=(np.array(point)-point1)[0:2]

    angle=self.Angle(angle_point,[1,0])
    print("angle:",angle)
    if(angle>90):
      angle=180-angle
    if(np.dot(angle_point,[0,1])<0):
      angle=-angle
    trans_angle=self.GetMarix_z(angle)

    point2 = [(point[0]+point1[0]+point3[0])/3,(point[1]+point1[1])/2,(point[2]+point1[2]+point3[2])/3]
    #a = [point2[0] - point3[0], point2[1] - point3[1], point2[2] - point3[2]]
    TransformTmp = slicer.util.getNode('变换_胫骨约束')
    # if slicer.modules.NoImageWelcomeWidget.judge == 'R':
    #   a[0]=-a[0]
    #   a[1] = -a[1]
    TtransTmp = np.array([[1, 0, 0, -point2[0]],
                    [0, 1, 0, -point2[1]-3],
                    [0, 0, 1, distance],
                    [0, 0, 0, 1]])

    #print('TtransTmp',TtransTmp,'a',a)
    #xzjz = self.GetMarix_z(-2)
    trans = np.dot(TtransTmp,trans_angle)
    TransformTmp.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans))
    #self.onJieGuJianXi()


  #胫骨变换合集
  def TibiaTrans(self):
      transform3 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_3'))
      transform4 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_4'))
      transform5 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_5'))
      transform_tmp = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_胫骨'))
      Trans = np.dot(np.dot(np.dot(transform3, transform4), transform_tmp),transform5)
      return Trans

  #推荐胫骨假体
  def SelectTibiaJiaTi(self):
    self.TibiaJieGu()
    PointPath = os.path.join(os.path.dirname(__file__), '假体库/a')
    #trans = self.TibiaTrans()
    # lujing = os.path.join(self.jiatiPath, 'Tibia-1-5.stl')
    # self.TibiaJiaTiload = slicer.util.loadModel(lujing)
    # Transform5 = slicer.util.getNode('变换_5')
    # self.TibiaJiaTiload.SetAndObserveTransformNodeID(Transform5.GetID())
    judge1=[]
    index1=[]
    
    list = ['1-5', '2', '2-5', '3', '4', '5']
    for i in range(0, len(list)):
        inputPoints=[]
        name = 'Tibia-' + list[i]
        lujing = os.path.join(PointPath,name+'.txt')
        print('lujing',lujing)
        point  =  np.loadtxt(lujing)
        TransformTmp = slicer.util.getNode('变换_胫骨约束')
        trans = slicer.util.arrayFromTransformMatrix(TransformTmp)
        trans_ni=np.linalg.inv(trans)
        for j in range(len(point)):
          point[j]=np.dot(trans_ni,[point[j][0],point[j][1],point[j][2],1])[0:3]
        inputModel=slicer.util.getNode('Tibia')
        surface_World = inputModel.GetPolyData()
        distanceFilter = vtk.vtkImplicitPolyDataDistance()
        distanceFilter.SetInput(surface_World)
        nOfFiducialPoints = 11
        distances = np.zeros(nOfFiducialPoints)
        for j in range(nOfFiducialPoints):
            point_World = point[j] 
            closestPointOnSurface_World = np.zeros(3)
            closestPointDistance = distanceFilter.EvaluateFunctionAndGetClosestPoint(point_World, closestPointOnSurface_World)
            distances[j] = closestPointDistance
        a=0
        #if list[i] == list[self.select]:
        if list[i] == list[3]:
            tmp = distances
        print('distances:',distances)
        # for j in range(nOfFiducialPoints):
        #     if distances[j]<0:
        #         a = a + 1

        if distances[0]+distances[4]<0 and  distances[2]+distances[7]<0 and distances[5]+distances[10]<0:
            a=10
        
        if list[i] == '1-5':
            dis = distances
            TransformTmp = slicer.util.getNode('变换_胫骨约束')
            c = slicer.util.arrayFromTransformMatrix(TransformTmp)
            c[1][3] = c[1][3] + (distances[10]) / 2
            TransformTmp.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(c))
                
        if a==10:
            sum = 0
            for j in range(nOfFiducialPoints):
                sum =sum + distances[j]
            judge1.append(sum)        
    
            index1.append(i)
          

      # if len(judge1)<1:
      #     TransformTmp = slicer.util.getNode('变换_胫骨')
      #     c =slicer.util.arrayFromTransformMatrix(TransformTmp)
      #     c[1][3]=c[1][3]+dis[10]
      #     TransformTmp.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(c))
      #     self.TibiaJtSelectNum=1
      #     self.SelectTibiaJiaTi()
      #     return 1
          

    if len(judge1)>=1:
        max_judge1=judge1.index(max(judge1))
        print('judge',judge1)
        print('index',index1)
        self.TibiaSelect = index1[max_judge1]
        if self.TibiaSelect - self.select >1:
            self.TibiaSelect = self.select+1
        elif self.select - self.TibiaSelect >1:
            self.TibiaSelect = self.TibiaSelect+1
    else:
        self.TibiaSelect = self.select

    Name = 'Tibia-'+list[self.TibiaSelect]
    # self.ui.TibiaJiaTi.setCurrentText(Name)
    self.TibiaJiaTi = Name
    # self.ui.JiaTiNameT.setText(Name)

      #self.AddKongBai()
      #设置表头文字颜色
      # self.ui.TibiaTableWidget.verticalHeaderItem(self.TibiaSelect).setForeground(qt.QBrush(qt.QColor(48,47,45)))
      # #设置表头背景颜色
      # self.ui.TibiaTableWidget.verticalHeaderItem(self.TibiaSelect).setBackground(qt.QColor(124,189,39))
      # self.ui.TibiaTableWidget.horizontalHeaderItem(self.select).setForeground(qt.QBrush(qt.QColor(48,47,45)))
      # self.ui.TibiaTableWidget.horizontalHeaderItem(self.select).setBackground(qt.QColor(124,189,39))
      # self.ui.TibiaTableWidget.item(self.TibiaSelect, self.select).setBackground(qt.QColor(124, 189, 39))
  #加载胫骨假体    
  def loadTibiaJiaTi(self, name):
    try:
      slicer.mrmlScene.RemoveNode(self.TibiaJiaTiload)
    except Exception as e:
      print(e) 
    lujing = os.path.join(self.jiatiPath, name + '.stl')
    print('name',name)
    
    self.TibiaJiaTiload = slicer.util.loadModel(lujing)
    self.TibiaJiaTiload.SetName(name)
    #胫骨切割
    slicer.modules.tibiapopup.widgetRepresentation().self().onConfirm()
    #将假体放在Transform约束变换下：
    # TtransformYueShu = slicer.util.getNode('变换_胫骨约束')
    # self.TibiaJiaTiload.SetAndObserveTransformNodeID(TtransformYueShu.GetID())



  #胫骨截骨调整
  def onAdjustment2(self):

    segs = slicer.util.getNodesByClass('vtkMRMLMarkupsFiducialNode')
    Name = []
    for i in range(0, len(segs)):
      a = segs[i]
      Name.append(a.GetName())
    if '胫骨截骨面' in Name:
        pass

    else:
      # 截骨面
      TibiaJieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', '胫骨截骨面')
      TibiaJieGu.AddControlPoint(30, 0, 0)
      TibiaJieGu.AddControlPoint(0, 30, 0)
      TibiaJieGu.AddControlPoint(0, 0, 0)
      slicer.util.getNode('胫骨截骨面').SetDisplayVisibility(False)

    #计算角度
    try:
      ras1, ras2, ras3, ras4 = [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]
      slicer.util.getNode('胫骨隆凸1').GetNthControlPointPositionWorld(0, ras1)
      slicer.util.getNode('内侧高点1').GetNthControlPointPositionWorld(0, ras2)
      slicer.util.getNode('外侧高点1').GetNthControlPointPositionWorld(0, ras3)
      slicer.util.getNode('踝穴中心1').GetNthControlPointPositionWorld(0, ras4)
      #胫骨后倾角
      TibiaJGM =self.GetTransPoint('胫骨截骨面')
      NGTY = self.TouYing(TibiaJGM, ras2)
      WGTY = self.TouYing(TibiaJGM, ras3)
      xl1=np.array([NGTY[0]-WGTY[0], NGTY[1]-WGTY[1], NGTY[2]-WGTY[2]])
      xl2=np.array([ras4[0]-ras1[0], ras4[1]-ras1[1], ras4[2]-ras1[2]])
      houqingjiao =self.Angle(xl1, xl2)
      self.TibiaHouQingJiao = 90-houqingjiao
      # 胫骨外旋角
      xl4 = np.array([ras2[0]-ras3[0], ras2[1]-ras3[1], ras2[2]-ras3[2]])
      self.TibiaWaiXuanJiao = self.Angle(xl1, xl4)
    except Exception as e:
      print(e)

  
  #设置胫骨三维视图注释
  def SetTibiaCameraTip(self):
    self.hideInformation()
    # 视图1按钮
    icon1A = qt.QIcon()
    icons1APath = os.path.join(self.iconsPath, '重置.png')
    icon1A.addPixmap(qt.QPixmap(icons1APath))
    self.TV1Button = qt.QPushButton(self.view1)
    self.TV1Button.setGeometry(5, 5, 41, 41)
    self.TV1Button.setIconSize(qt.QSize(41, 41))
    self.TV1Button.setIcon(icon1A)
    self.TV1Button.setFlat(True)
    self.TV1Button.setStyleSheet("QPushButton{border:none;background:transparent;color:rgba(0,0,0,0);}")
    self.TV1Button.connect('clicked(bool)', self.onTV1Button)
    self.TV1Button.setToolTip('锁定')
    self.TV1Button.show()
    # 视图2按钮
    icon2A = qt.QIcon()
    icons2APath = os.path.join(self.iconsPath, '箭头.png')
    icon2A.addPixmap(qt.QPixmap(icons2APath))
    self.TV2Button = qt.QPushButton(self.view2)
    self.TV2Button.setGeometry(5, 5, 41, 41)
    self.TV2Button.setIconSize(qt.QSize(41, 41))
    self.TV2Button.setIcon(icon2A)
    self.TV2Button.setFlat(True)
    self.TV2Button.setStyleSheet("QPushButton{border:none;background:transparent;}")
    self.TV2Button.connect('clicked(bool)', self.onTV2Button)
    self.TV2Button.show()
    # 视图3按钮
    icon3A = qt.QIcon()
    icons3APath = os.path.join(self.iconsPath, '箭头.png')
    icon3A.addPixmap(qt.QPixmap(icons3APath))
    self.TV3Button = qt.QPushButton(self.view3)
    self.TV3Button.setGeometry(5, 5, 41, 41)
    self.TV3Button.setIconSize(qt.QSize(41, 41))
    self.TV3Button.setIcon(icon3A)
    self.TV3Button.setFlat(True)
    self.TV3Button.setStyleSheet("QPushButton{border:none;background:transparent;}")
    self.TV3Button.connect('clicked(bool)', self.onTV3Button)
    self.TV3Button.show()

    # 设置相机
    self.TCamera1(self.view1)
    self.TCamera2(self.view2)
    self.TCamera3(self.view3)

    cameraNode = self.view1.cameraNode()
    cameraNode2 = self.view2.cameraNode()
    if slicer.modules.NoImageWelcomeWidget.judge == 'L':
      if (cameraNode.GetName() == 'TC1'):
          if (cameraNode2.GetName() == 'TC2'):
              self.TCamera1Tip(self.view1)
              self.TCamera2Tip(self.view2)
              self.TCamera3Tip(self.view3)
          else:
              self.TCamera1Tip(self.view1)
              self.TCamera2Tip(self.view3)
              self.TCamera3Tip(self.view2)

      elif (cameraNode.GetName() == 'TC2'):
          if (cameraNode2.GetName() == 'TC1'):
              self.TCamera1Tip(self.view2)
              self.TCamera2Tip(self.view1)
              self.TCamera3Tip(self.view3)
          else:
              self.TCamera1Tip(self.view2)
              self.TCamera2Tip(self.view3)
              self.TCamera3Tip(self.view1)
      else:
          if (cameraNode2.GetName() == 'TC2'):
              self.TCamera1Tip(self.view3)
              self.TCamera2Tip(self.view2)
              self.TCamera3Tip(self.view1)
          else:
              self.TCamera1Tip(self.view3)
              self.TCamera2Tip(self.view1)
              self.TCamera3Tip(self.view2)
    else:
      if (cameraNode.GetName() == 'TC1'):
          if (cameraNode2.GetName() == 'TC2'):
              self.TCamera1TipRight(self.view1)
              self.TCamera2Tip(self.view2)
              self.TCamera3TipRight(self.view3)
          else:
              self.TCamera1TipRight(self.view1)
              self.TCamera2Tip(self.view3)
              self.TCamera3TipRight(self.view2)
      elif (cameraNode.GetName() == 'TC2'):
          if (cameraNode2.GetName() == 'TC1'):
              self.TCamera1TipRight(self.view2)
              self.TCamera2Tip(self.view1)
              self.TCamera3TipRight(self.view3)
          else:
              self.TCamera1TipRight(self.view2)
              self.TCamera2Tip(self.view3)
              self.TCamera3TipRight(self.view1)
      else:
          if (cameraNode2.GetName() == 'TC2'):
              self.TCamera1TipRight(self.view3)
              self.TCamera2Tip(self.view2)
              self.TCamera3TipRight(self.view1)
          else:
              self.TCamera1TipRight(self.view3)
              self.TCamera2Tip(self.view1)
              self.TCamera3TipRight(self.view2)

  #胫骨视图选择
  def onTibiaViewSelect(self):
    self.HideAll()
    self.ui.PopupWidget.setVisible(True)
    self.hideInformation()
    self.ThreeDState()
    self.ui.PopupWidget.setMinimumHeight(650)
    slicer.modules.tibiaviewselect.widgetRepresentation().setParent(self.ui.PopupWidget)
    slicer.modules.tibiaviewselect.widgetRepresentation().setGeometry(-10,-10,624,624)
    slicer.modules.tibiaviewselect.widgetRepresentation().show()
    self.TibiaButtonChecked(self.ui.ViewChoose2)

  #胫骨重置
  def onReset2(self):
    message = qt.QMessageBox(qt.QMessageBox.Information,'重置',"是否要重置胫骨的方案？",qt.QMessageBox.Ok|qt.QMessageBox.Cancel)
    message.button(qt.QMessageBox().Ok).setText('是')
    message.button(qt.QMessageBox().Cancel).setText('否')
    c= message.exec()
    if c == qt.QMessageBox.Ok:
      self.TibiaButtonChecked(self.ui.ReSet2)
      slicer.app.setOverrideCursor(qt.Qt.WaitCursor)  # 光标变成圆圈
      self.DeleteNode('变换_3')
      self.DeleteNode('变换_4')
      self.DeleteNode('变换_5')
      self.DeleteNode('变换_胫骨')
      self.DeleteNode('变换_约束')
      self.DeleteNode(self.TibiaJiaTiload.GetName())
      self.DeleteNode('胫骨近端切割')
      self.DeleteNode('胫骨截骨面')
      self.DeleteNode('胫骨近端')
      self.DeleteNode('DynamicModeler_1')
      self.DeleteNode('胫骨切割')
      self.DeleteNode('切割6')
      self.DeleteNode('部件6')
      self.DeleteNode('动态切割6')
      slicer.app.restoreOverrideCursor()  # 变回光标原来的形状
      #显示点
      self.ShowNode('外侧高点')
      self.ShowNode('内侧高点')
      self.ShowNode('胫骨隆凸')
      self.ShowNode('胫骨结节')
      self.ShowNode('踝穴中心')
      #显示胫骨并将胫骨透明化
      Tibia = slicer.util.getNode('Tibia')
      Tibia.SetDisplayVisibility(1)
      Tibia.GetDisplayNode().SetOpacity(0.2)
      # 回到解剖标志
      self.ui.Parameter2.click()
    elif c == qt.QMessageBox.Canel:
      self.ui.ReSet2.setChecked(False)
  #--------------head-显示/隐藏---------------------------------------------
  # 截骨调整-截骨面
  def onBoneButton(self):
    if self.currentModel == 3:
      Bone = slicer.util.getNode('股骨切割')
      FemurYD = slicer.util.getNode('股骨远端')
      self.TibiaShowHide2()
      if self.ui.BoneButton.isChecked():
        self.ui.TransparentButton.setEnabled(False)
        Bone.SetDisplayVisibility(1)
        FemurYD.SetDisplayVisibility(0)
      else:
        self.ui.TransparentButton.setEnabled(True)
        Bone.SetDisplayVisibility(0)
        FemurYD.SetDisplayVisibility(1)

    elif self.currentModel == 4:
      Bone = slicer.util.getNode('胫骨切割')
      TibiaJD = slicer.util.getNode('胫骨近端')
      self.FemurShowHide2()
      if self.ui.BoneButton.isChecked():
        self.ui.TransparentButton.setEnabled(False)
        Bone.SetDisplayVisibility(1)
        TibiaJD.SetDisplayVisibility(0)
      else:
        self.ui.TransparentButton.setEnabled(True)
        Bone.SetDisplayVisibility(0)
        TibiaJD.SetDisplayVisibility(1)
  # 截骨调整-假体
  def onJiaTiButton(self):
    if self.currentModel == 3:
      self.TibiaJiaTiShowHide()
      if self.jiatiload.GetDisplayVisibility() == 1:
          self.jiatiload.SetDisplayVisibility(0)
      else:
          self.jiatiload.SetDisplayVisibility(1)
    elif self.currentModel == 4:
      self.FemurJiaTiShowHide()
      if self.TibiaJiaTiload.GetDisplayVisibility() == 1:
          self.TibiaJiaTiload.SetDisplayVisibility(0)
      else:
          self.TibiaJiaTiload.SetDisplayVisibility(1)
  # 截骨调整-标记点
  def onMarkerButton(self):
    if self.currentModel == 3:
      self.TibiaMarkShowHide()
      if self.ui.MarkerButton.isChecked():
        self.ShowNode('A点')
        self.ShowNode('内侧后髁')
        self.ShowNode('外侧后髁')
        self.ShowNode('外侧远端')
        self.ShowNode('内侧远端')
        self.ShowNode('外侧凸点')
        self.ShowNode('内侧凹点')
        self.ShowNode('开髓点')
        self.ShowNode('外侧皮质高点')

      else:
        self.HideNode('A点')
        self.HideNode('开髓点')
        self.HideNode('内侧后髁')
        self.HideNode('外侧后髁')
        self.HideNode('外侧远端')
        self.HideNode('内侧远端')
        self.HideNode('外侧凸点')
        self.HideNode('内侧凹点')
        self.HideNode('外侧皮质高点')

    elif self.currentModel == 4:
      self.FmeurMarkShowHide()
      if self.ui.MarkerButton.isChecked():
        self.ShowNode('外侧高点')
        self.ShowNode('内侧高点')
        self.ShowNode('胫骨隆凸')
        self.ShowNode('胫骨结节')
      else:
        self.HideNode('外侧高点')
        self.HideNode('内侧高点')
        self.HideNode('胫骨隆凸')
        self.HideNode('胫骨结节')
  # 截骨调整-透明显示
  def onTransparentButton(self):
    if self.currentModel == 3:
      self.TibiaTransparentShowHide()
      Femur = slicer.util.getNode('股骨远端')
      Femur.SetDisplayVisibility(1)
      if self.ui.TransparentButton.isChecked():
          self.ui.BoneButton.setEnabled(False)
          Femur.GetDisplayNode().SetOpacity(0.2)
      else:
          self.ui.BoneButton.setEnabled(True)
          Femur.GetDisplayNode().SetOpacity(1.0)


    elif self.currentModel == 4:
      self.FemurTransparentShowHide()
      Tibia = slicer.util.getNode('胫骨近端')
      Tibia.SetDisplayVisibility(1)
      if self.ui.TransparentButton.isChecked():
          self.ui.BoneButton.setEnabled(False)
          Tibia.GetDisplayNode().SetOpacity(0.2)
      else:
          self.ui.BoneButton.setEnabled(True)
          Tibia.GetDisplayNode().SetOpacity(1.0)
  
  # def InitHeadWidget(self):
  #   self.ui.FemurSwitch.setVisible(False)
  #   self.ui.TibiaSwitch.setVisible(False)
  #   self.ui.FemurR.setVisible(False)
  #   self.ui.FemurL.setVisible(False)
  #   self.ui.TibiaJiaTi.setVisible(False)
  #   self.ui.FemurShowHide.setVisible(False)
  #   self.ui.TibiaShowHide.setVisible(False)
  #   if self.currentModel == 3:
  #     self.ui.TibiaSwitch.setVisible(True)
  #     self.ui.TibiaShowHide.setVisible(True)
  #     self.ui.TibiaJiaTi.setVisible(True)
  #     if slicer.modules.NoImageWelcomeWidget.judge == 'L':
  #       self.ui.FemurL.setVisible(True)
  #     else:
  #       self.ui.FemurR.setVisible(True)
  #   else:
  #     self.ui.FemurSwitch.setVisible(True)
  #     self.ui.TibiaJiaTi.setVisible(True)
  #     self.ui.FemurShowHide.setVisible(True)
  #     if slicer.modules.NoImageWelcomeWidget.judge == 'L':
  #       self.ui.FemurL.setVisible(True)
  #     else:
  #       self.ui.FemurR.setVisible(True)

  def onFemurR(self,index):
    # print(index)
    # print(self.ui.FemurR.currentText)
    # name = self.ui.FemurR.currentText
    name = self.FemurR
    self.ui.label_21.setText(self.FemurR)
    self.loadJiaTi(name)
    if self.ui.BoneButton.checked:
      slicer.modules.PopupWidget.ui.Confirm.click()

    #self.ShowHide()

  def onFemurL(self,index):
    # print(index)
    # print(self.ui.FemurL.currentText) 
    # name = self.ui.FemurL.currentText
    name = self.FemurL
    self.ui.label_21.setText(self.FemurL)
    self.loadJiaTi(name)
    if self.ui.BoneButton.checked:
      slicer.modules.PopupWidget.ui.Confirm.click()

    #self.ShowHide()
  
  def onTibiaJiaTi(self,index):
    # print(index)
    # print(self.ui.TibiaJiaTi.currentText)
    name = self.TibiaJiaTi
    self.ui.label_23.setText(self.TibiaJiaTi)
    self.loadTibiaJiaTi(name)
    # if self.ui.BoneButton.checked:
    #   slicer.modules.TibiaPopupWidget.ui.xMoveButton1.click()
    #   self.ui.BoneButton.click()
    #   self.ui.BoneButton.click()

    # try:
    #   self.ShowHide()
    # except:
    #   print("没有胫骨切割")

  def onFemurSwitch(self):
    self.currentModel = 3
    self.WidgetShow(self.currentModel)
    self.ui.Adjustment.click()
  
  def onTibiaSwitch(self):
    self.currentModel = 4
    self.WidgetShow(self.currentModel)
    self.ui.Adjustment2.click()
    
  def onFemurShowHide(self):
    self.FemurShowHide2()
    self.FemurJiaTiShowHide()
    self.FmeurMarkShowHide()
    self.FemurTransparentShowHide()
  
  def onTibiaShowHide(self):
    self.TibiaShowHide2()
    self.TibiaJiaTiShowHide()
    self.TibiaMarkShowHide()
    self.TibiaTransparentShowHide()

  
  def TibiaShowHide2(self):
    if self.ui.TibiaShowHide.checked:
      if self.ui.BoneButton.checked:
        self.ShowNode('胫骨切割')
        self.HideNode('胫骨近端')
      else:
        self.ShowNode('胫骨近端')
        self.HideNode('胫骨切割')
    else:
        self.HideNode('胫骨近端')
        self.HideNode('胫骨切割')
  
  def FemurShowHide2(self):
    if self.ui.FemurShowHide.checked:
      if self.ui.BoneButton.checked:
        self.ShowNode('股骨切割')
        self.HideNode('股骨远端')
      else:
        self.HideNode('股骨切割')
        self.ShowNode('股骨远端')
    else:
        self.HideNode('股骨切割')
        self.HideNode('股骨远端')

  def FemurJiaTiShowHide(self):
    if self.ui.FemurShowHide.checked:
      if self.ui.JiaTiButton.checked:
        self.jiatiload.SetDisplayVisibility(1)
      else:
        self.jiatiload.SetDisplayVisibility(0)
    else:
      self.jiatiload.SetDisplayVisibility(0)
  def TibiaJiaTiShowHide(self):
    if self.ui.TibiaShowHide.checked:
      if self.ui.JiaTiButton.checked:
        self.TibiaJiaTiload.SetDisplayVisibility(1)
      else:
        self.TibiaJiaTiload.SetDisplayVisibility(0)
    else:
      self.TibiaJiaTiload.SetDisplayVisibility(0)
  def FmeurMarkShowHide(self):
    if self.ui.FemurShowHide.checked:
      if self.ui.MarkerButton.checked:
        self.ShowNode('A点')
        self.ShowNode('内侧后髁')
        self.ShowNode('外侧后髁')
        self.ShowNode('外侧远端')
        self.ShowNode('内侧远端')
        self.ShowNode('外侧凸点')
        self.ShowNode('内侧凹点')
        self.ShowNode('开髓点')
        self.ShowNode('外侧皮质高点')
      else:
        self.HideNode('A点')
        self.HideNode('开髓点')
        self.HideNode('内侧后髁')
        self.HideNode('外侧后髁')
        self.HideNode('外侧远端')
        self.HideNode('内侧远端')
        self.HideNode('外侧凸点')
        self.HideNode('内侧凹点')
        self.HideNode('外侧皮质高点')
    else:
      self.HideNode('A点')
      self.HideNode('开髓点')
      self.HideNode('内侧后髁')
      self.HideNode('外侧后髁')
      self.HideNode('外侧远端')
      self.HideNode('内侧远端')
      self.HideNode('外侧凸点')
      self.HideNode('内侧凹点')
      self.HideNode('外侧皮质高点')
  def TibiaMarkShowHide(self):
    if self.ui.TibiaShowHide.checked:
      if self.ui.MarkerButton.checked:
        self.ShowNode('外侧高点')
        self.ShowNode('内侧高点')
        self.ShowNode('胫骨隆凸')
        self.ShowNode('胫骨结节')
      else:
        self.HideNode('外侧高点')
        self.HideNode('内侧高点')
        self.HideNode('胫骨隆凸')
        self.HideNode('胫骨结节')
    else:
      self.HideNode('外侧高点')
      self.HideNode('内侧高点')
      self.HideNode('胫骨隆凸')
      self.HideNode('胫骨结节')
  def FemurTransparentShowHide(self):
    Femur = slicer.util.getNode('股骨远端')
    Femur.SetDisplayVisibility(1)
    if self.ui.FemurShowHide.checked:
      if self.ui.TransparentButton.checked:
          Femur.GetDisplayNode().SetOpacity(0.2)
      else:
        Femur.GetDisplayNode().SetOpacity(1)
    else:
      Femur.SetDisplayVisibility(0)
  def TibiaTransparentShowHide(self):
    Tibia = slicer.util.getNode('胫骨近端')
    Tibia.SetDisplayVisibility(1)
    if self.ui.TibiaShowHide.checked:
      if self.ui.TransparentButton.checked:
          Tibia.GetDisplayNode().SetOpacity(0.2)
      else:
        Tibia.GetDisplayNode().SetOpacity(1)
    else:
      Tibia.SetDisplayVisibility(0)
  
  #设置模型在第三个三维视图中是否显示 0-不显示 1-显示
  def ThreeDViewShowHide(self,name,index):
    displayNode = slicer.util.getNode(name).GetDisplayNode()
    threeDViewIDs = [node.GetID() for node in slicer.util.getNodesByClass('vtkMRMLViewNode')]
    if index == 0:
      displayNode.SetViewNodeIDs(['vtkMRMLViewNode1','vtkMRMLViewNode2'])
    else:
      displayNode.SetViewNodeIDs(threeDViewIDs)
  
  def ShowHide(self):
    if self.ui.Adjustment.checked:
      self.ThreeDViewShowHide('胫骨切割',0)
      self.ThreeDViewShowHide('胫骨近端',0)
      self.ThreeDViewShowHide(self.TibiaJiaTiload.GetName(),0)
      self.ThreeDViewShowHide('股骨切割',1)
      self.ThreeDViewShowHide('股骨远端',1)
      self.ThreeDViewShowHide(self.jiatiload.GetName(),1)
    elif self.ui.Adjustment2.checked:
      self.ThreeDViewShowHide('胫骨切割',1)
      self.ThreeDViewShowHide('胫骨近端',1)
      self.ThreeDViewShowHide(self.TibiaJiaTiload.GetName(),1)
      self.ThreeDViewShowHide(self.jiatiload.GetName(),0)
      self.ThreeDViewShowHide('股骨切割',0)
      self.ThreeDViewShowHide('股骨远端',0)
    elif self.currentModel == 5:
      displayNode = slicer.util.getNode('胫骨近端').GetDisplayNode()
      displayNode.SetViewNodeIDs(['vtkMRMLViewNode1'])
      displayNode = slicer.util.getNode('股骨远端').GetDisplayNode()
      displayNode.SetViewNodeIDs(['vtkMRMLViewNode1'])
      displayNode = slicer.util.getNode('股骨切割').GetDisplayNode()
      displayNode.SetViewNodeIDs(['vtkMRMLViewNode2','vtkMRMLViewNode3'])
      displayNode = slicer.util.getNode('胫骨切割').GetDisplayNode()
      displayNode.SetViewNodeIDs(['vtkMRMLViewNode2','vtkMRMLViewNode4'])
      self.jiatiload.GetDisplayNode().SetViewNodeIDs(['vtkMRMLViewNode2','vtkMRMLViewNode3'])
      self.TibiaJiaTiload.GetDisplayNode().SetViewNodeIDs(['vtkMRMLViewNode2','vtkMRMLViewNode4'])
      self.ChenDian.GetDisplayNode().SetViewNodeIDs(['vtkMRMLViewNode2'])
    else:
      self.ThreeDViewShowHide('胫骨切割',1)
      self.ThreeDViewShowHide('胫骨近端',1)
      self.ThreeDViewShowHide('股骨切割',1)
      self.ThreeDViewShowHide('股骨远端',1)
      self.ThreeDViewShowHide(self.jiatiload.GetName(),1)
      self.ThreeDViewShowHide(self.TibiaJiaTiload.GetName(),1)

  #--------------------------报告-----------------------------------
  #加载衬垫
  def loadChenDian(self):
    if self.TibiaJiaTiload.GetName() =='Tibia-1-5':
      try:
          slicer.mrmlScene.RemoveNode(self.ChenDian)

      except Exception as e:
          print(e)
      lujing = os.path.join(self.jiatiPath, 'Insert-1-5.stl')
      self.ChenDian = slicer.util.loadModel(lujing)
      self.ChenDian.SetName('Insert-1-5')
    elif self.TibiaJiaTiload.GetName() =='Tibia-2':
      try:
        slicer.mrmlScene.RemoveNode(self.ChenDian)

      except Exception as e:
          print(e)
      lujing = os.path.join(self.jiatiPath, 'Insert-2.stl')
      self.ChenDian = slicer.util.loadModel(lujing)
      self.ChenDian.SetName('Insert-2')
    elif self.TibiaJiaTiload.GetName() =='Tibia-2-5':
      try:
          slicer.mrmlScene.RemoveNode(self.ChenDian)

      except Exception as e:
          print(e)
      lujing = os.path.join(self.jiatiPath, 'Insert-2-5.stl')
      self.ChenDian = slicer.util.loadModel(lujing)
      self.ChenDian.SetName('Insert-2-5')
    elif self.TibiaJiaTiload.GetName() =='Tibia-3':
      try:
          slicer.mrmlScene.RemoveNode(self.ChenDian)

      except Exception as e:
          print(e)
      lujing = os.path.join(self.jiatiPath, 'Insert-3.stl')
      self.ChenDian = slicer.util.loadModel(lujing)
      self.ChenDian.SetName('Insert-3')
    elif self.TibiaJiaTiload.GetName() =='Tibia-4':
      try:
          slicer.mrmlScene.RemoveNode(self.ChenDian)

      except Exception as e:
          print(e)
      lujing = os.path.join(self.jiatiPath, 'Insert-4.stl')
      self.ChenDian = slicer.util.loadModel(lujing)
      self.ChenDian.SetName('Insert-4')
    elif self.TibiaJiaTiload.GetName() =='Tibia-3':
      try:
          slicer.mrmlScene.RemoveNode(self.ChenDian)

      except Exception as e:
          print(e)
      lujing = os.path.join(self.jiatiPath, 'Insert-5.stl')
      self.ChenDian = slicer.util.loadModel(lujing)
      self.ChenDian.SetName('Insert-5')
  #调直
  def onJieTu(self):
    self.ReportButtonChecked(self.ui.JieTu)
    import time
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    self.HidePart()
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    slicer.util.getNode('胫骨近端').SetAndObserveTransformNodeID(shNode.GetID())
    self.ShowNode('股骨远端')
    self.ShowNode('胫骨近端')
    time.sleep(1)
    renderWindow = slicer.app.layoutManager().threeDWidget('View1').threeDView().renderWindow()
    renderWindow.SetAlphaBitPlanes(1)
    wti = vtk.vtkWindowToImageFilter()
    wti.SetInputBufferTypeToRGBA()
    wti.SetInput(renderWindow)
    writer = vtk.vtkPNGWriter()
    path = slicer.modules.report.path
    lujing1 = path[0:-9] + 'Resources/Icons/手术报告-3.png'
    writer.SetFileName(lujing1)
    writer.SetInputConnection(wti.GetOutputPort())
    writer.Write()
    print('手术报告-3已截图')
    self.HidePart()
    self.ShowNode('股骨切割')
    self.ShowNode('胫骨切割')
    self.jiatiload.SetDisplayVisibility(True)
    self.TibiaJiaTiload.SetDisplayVisibility(True)
    self.ChenDian.SetDisplayVisibility(True)
    #self.ShuZhi()
    time.sleep(1)
    renderWindow = slicer.app.layoutManager().threeDWidget('View1').threeDView().renderWindow()
    renderWindow.SetAlphaBitPlanes(1)
    wti = vtk.vtkWindowToImageFilter()
    wti.SetInputBufferTypeToRGBA()
    wti.SetInput(renderWindow)
    writer = vtk.vtkPNGWriter()
    path = slicer.modules.report.path
    lujing2 = path[0:-9] + 'Resources/Icons/手术报告-4.png'
    writer.SetFileName(lujing2)
    writer.SetInputConnection(wti.GetOutputPort())
    writer.Write()
    print('手术报告-4已截图')

    self.Camera3(self.view3)
    self.ShowNode('股骨切割')
    self.jiatiload.SetDisplayVisibility(True)
    self.ChenDian.SetDisplayVisibility(False)
    self.HideNode('胫骨切割')
    self.TibiaJiaTiload.SetDisplayVisibility(False)
    time.sleep(1)

    renderWindow = slicer.app.layoutManager().threeDWidget('View3').threeDView().renderWindow()
    renderWindow.SetAlphaBitPlanes(1)
    wti = vtk.vtkWindowToImageFilter()
    wti.SetInputBufferTypeToRGBA()
    wti.SetInput(renderWindow)
    writer = vtk.vtkPNGWriter()
    path = slicer.modules.report.path
    lujing2 = path[0:-9] + 'Resources/Icons/手术报告-1.png'
    writer.SetFileName(lujing2)
    writer.SetInputConnection(wti.GetOutputPort())
    writer.Write()
    print('手术报告-1已截图')

    view4 = slicer.app.layoutManager().threeDWidget('View4').threeDView()
    self.TCamera3(view4)
    self.HideNode('股骨切割')
    self.jiatiload.SetDisplayVisibility(False)
    self.ChenDian.SetDisplayVisibility(False)
    self.ShowNode('胫骨切割')
    self.TibiaJiaTiload.SetDisplayVisibility(True)
    time.sleep(1)

    renderWindow = slicer.app.layoutManager().threeDWidget('View4').threeDView().renderWindow()
    renderWindow.SetAlphaBitPlanes(1)
    wti = vtk.vtkWindowToImageFilter()
    wti.SetInputBufferTypeToRGBA()
    wti.SetInput(renderWindow)
    writer = vtk.vtkPNGWriter()
    path = slicer.modules.report.path
    lujing2 = path[0:-9] + 'Resources/Icons/手术报告-2.png'
    writer.SetFileName(lujing2)
    writer.SetInputConnection(wti.GetOutputPort())
    writer.Write()
    print('手术报告-2已截图')

    print('截图完成')
    self.ShowNode('股骨切割')
    self.jiatiload.SetDisplayVisibility(True)
    self.ShowNode('胫骨切割')
    self.TibiaJiaTiload.SetDisplayVisibility(True)
    self.ChenDian.SetDisplayVisibility(True)
    slicer.app.restoreOverrideCursor()
      
  #在组合中将股骨和胫骨调整为竖直状态
  def ShuZhi(self):
    #股骨变换
    try:
      slicer.util.getNode('变换_6')
    except:
      transformNode = slicer.util.getNode('变换')
      trans = slicer.util.arrayFromTransformMatrix(transformNode)
      transformNode1 = slicer.util.getNode('变换_1')
      trans1 = slicer.util.arrayFromTransformMatrix(transformNode1)
      transformNodeTmp = slicer.util.getNode('变换_临时')
      transTmp = slicer.util.arrayFromTransformMatrix(transformNodeTmp)
      transformNode2 = slicer.util.getNode('变换_2')
      trans2 = slicer.util.arrayFromTransformMatrix(transformNode2)
      transformNodeR = slicer.util.getNode('变换_R')
      transR = slicer.util.arrayFromTransformMatrix(transformNodeR)
      #胫骨变换
      transformNode3 = slicer.util.getNode('变换_3')
      trans3 = slicer.util.arrayFromTransformMatrix(transformNode3)
      transformNode4 = slicer.util.getNode('变换_4')
      trans4 = slicer.util.arrayFromTransformMatrix(transformNode4)
      transformNodeTib = slicer.util.getNode('变换_胫骨')
      transTib = slicer.util.arrayFromTransformMatrix(transformNodeTib)
      transformNode5 = slicer.util.getNode('变换_5')
      trans5 = slicer.util.arrayFromTransformMatrix(transformNode5)
      transformNodeYueShu = slicer.util.getNode('变换_约束')
      transYueShu = slicer.util.arrayFromTransformMatrix(transformNodeYueShu)

      #股骨变换相乘
      FemurTrans = np.dot(np.dot(np.dot(np.dot(trans,trans1),transTmp),trans2),transR)
      #胫骨变换相乘
      TibiaTrans = np.dot(np.dot(np.dot(np.dot(trans3,trans4),transTib),trans5),transYueShu)
      # 胫骨变换矩阵求逆
      TibiaTrans_ni=np.linalg.inv(TibiaTrans)
      trans_1 = np.array([[1, 0, 0, 0],
                            [0, 1, 0, -10],
                            [0, 0, 1, -18],
                            [0, 0, 0, 1]])
      TibiaTrans_ni=np.dot(trans_1,TibiaTrans_ni)
      #FemurTrans[2][3]=FemurTrans[2][3]-18
      # FemurTrans[1][3]=FemurTrans[1][3]+10

      xzjz=np.dot(FemurTrans,TibiaTrans_ni)
      Ttransform6 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '变换_6')
      Ttransform6.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(xzjz))
      #将变换6放到胫骨变换的顶层，即变换3的上一层
      transformNode3.SetAndObserveTransformNodeID(Ttransform6.GetID())
      slicer.util.getNode('胫骨切割').SetAndObserveTransformNodeID(Ttransform6.GetID())
      slicer.util.getNode('胫骨近端').SetAndObserveTransformNodeID(Ttransform6.GetID())

  #CT
  def onCTReport(self):
    if self.ui.CTReport.checked:
      self.HideAll()
      self.ReportButtonChecked(self.ui.CTReport)
      self.ui.OperationPlanWidget.setVisible(True)
      self.ui.ReportWidget.setVisible(True)
      self.ThreeDViewAndImageWidget(0)
      for i in range (0,len(self.noimageWidget.findChildren('QLabel'))):
        self.noimageWidget.findChildren('QLabel')[-1].delete()

      slicer.modules.report.widgetRepresentation().setParent(self.noimageWidget)
      # 将手术报告UI设置为与mywidget同宽高
      slicer.modules.report.widgetRepresentation().resize(self.noimageWidget.width, self.noimageWidget.height)
      slicer.modules.report.widgetRepresentation().show()
      Logo1 = slicer.modules.ReportWidget.ui.Logo
      pixmap = qt.QPixmap(self.iconsPath+'/Logo.png')
      Logo1.setPixmap(pixmap)
      try:
      #将姓名添加到姓名编辑处
        self.ui.NameEdit.setText(slicer.modules.NoImageWelcomeWidget.ui.NameEdit.text)
      except Exception as e:
        print(e)
    else:
      slicer.modules.report.widgetRepresentation().setParent(None)
      self.ui.ReportWidget.setVisible(False)
      self.ThreeDViewAndImageWidget(2)
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourOverFourView)

  #MRI
  def onMRIReport(self):
    self.HideAll()
    self.ReportButtonChecked(self.ui.MRIReport)
    slicer.modules.report.widgetRepresentation().hide()
  
  #获取路径
  def onPath(self):
    filePath = qt.QFileDialog.getExistingDirectory(self.ui.NoImage, '保存手术报告路径', 'D:/Data')
    self.ui.path.setText(filePath)
  
  #对手术报告截图保存+保存工程文件
  def onConfirmReport(self):
    # 保存截图
    self.ui.SaveTip.setText('请稍候......')
    from PIL import Image
    import os
    import os.path
    img = qt.QPixmap.grabWidget(slicer.modules.report.widgetRepresentation()).toImage()
    luJing = self.ui.path.text + '/' + self.ui.NameEdit.text + '.png'
    img.save(luJing)
    im = Image.open(luJing)
    out = im.transpose(Image.ROTATE_90)
    out.save(luJing)
    slicer.util.pip_install('reportlab==3.6.5')
    pdf_path = self.ui.path.text + '/' + self.ui.NameEdit.text + '.pdf'
    self.PNG_PDF(luJing, pdf_path)
    os.remove(luJing)

    if self.ui.checkBox.isChecked():
      #保存工程文件
      import zipfile
      import os
      #UID = slicer.modules.Case_mainWidget.UID
      UID = ""
      temppath = self.FilePath+'/'+str(UID)+'手术规划' + '/kneetmppath'
      # 新建目录
      try:
          os.makedirs(temppath)
      except Exception as e:
          print(e)
      #股骨变换
      transformNode = slicer.util.getNode('变换')
      trans = slicer.util.arrayFromTransformMatrix(transformNode)
      transformNode1 = slicer.util.getNode('变换_1')
      trans1 = slicer.util.arrayFromTransformMatrix(transformNode1)
      transformNodeTmp = slicer.util.getNode('变换_临时')
      transTmp = slicer.util.arrayFromTransformMatrix(transformNodeTmp)
      transformNode2 = slicer.util.getNode('变换_2')
      trans2 = slicer.util.arrayFromTransformMatrix(transformNode2)
      transformNodeR = slicer.util.getNode('变换_R')
      transR = slicer.util.arrayFromTransformMatrix(transformNodeR)
      #胫骨变换
      transformNode6 = slicer.util.getNode('变换_6')
      trans6 = slicer.util.arrayFromTransformMatrix(transformNode6)
      transformNode3 = slicer.util.getNode('变换_3')
      trans3 = slicer.util.arrayFromTransformMatrix(transformNode3)
      transformNode4 = slicer.util.getNode('变换_4')
      trans4 = slicer.util.arrayFromTransformMatrix(transformNode4)
      transformNodeTib = slicer.util.getNode('变换_胫骨')
      transTib = slicer.util.arrayFromTransformMatrix(transformNodeTib)
      transformNode5 = slicer.util.getNode('变换_5')
      trans5 = slicer.util.arrayFromTransformMatrix(transformNode5)
      transformNodeYueShu = slicer.util.getNode('变换_约束')
      transYueShu = slicer.util.arrayFromTransformMatrix(transformNodeYueShu)

      tr = np.vstack((trans, trans1, transTmp, trans2, transR, trans6, trans3, trans4, transTib, trans5, transYueShu))
      points = np.empty([17, 3])
      Femur = self.jiatiload.GetName()
      Tibia = self.TibiaJiaTiload.GetName()
      dian = ["股骨头球心", "开髓点", '外侧凸点', '内侧凹点', '胫骨隆凸', '胫骨结节', '踝穴中心', 'H点', 'A点', '内侧后髁', '外侧后髁', '内侧远端', '外侧远端', '内侧高点', '外侧高点', '内侧凸点','外侧皮质高点']

      with open(temppath + '/Femur.txt', 'w') as f:
        np.savetxt(f, tr, fmt='%6f')
        for j in range(17):
            slicer.util.getNode(dian[j]).GetNthFiducialPosition(0, points[j])
        np.savetxt(f, points, fmt='%6f', delimiter=' ')
        f.write(Femur + "\n")
        f.write(Tibia + "\n")
        f.write("外侧远端" + str(slicer.modules.PopupWidget.FemurWaiCeYuanDuan)+ "\n")
        f.write("内侧远端" + str(slicer.modules.PopupWidget.FemurNeiCeYuanDuan) + "\n")
        f.write("外侧后髁" + str(slicer.modules.PopupWidget.FemurWaiCeHouKe) + "\n")
        f.write("内侧后髁" + str(slicer.modules.PopupWidget.FemurNeiCeHouKe) + "\n")
        f.write("外侧平台" + str(slicer.modules.TibiaPopupWidget.TibiaWaiCeJieGu) + "\n")
        f.write("内侧平台" + str(slicer.modules.TibiaPopupWidget.TibiaNeiCeJieGu) + "\n")

      f.close()
      models = ['Femur', 'Tibia', '股骨远端', '胫骨近端', '部件1', '部件2', '部件3', '部件4', '部件5', '部件6', '股骨切割', '胫骨切割']
      for i in range(0, 12):
          saveVolumeNode = slicer.util.getNode(models[i])
          myStorageNode = saveVolumeNode.CreateDefaultStorageNode()
          myStorageNode.SetFileName(temppath + '/' + models[i] + '.stl')
          myStorageNode.WriteData(saveVolumeNode)

      # 生成压缩文件
      ysPath=self.FilePath +'/'+str(UID)+'手术规划'+'.ttkx'
      z = zipfile.ZipFile(ysPath, 'w', zipfile.ZIP_DEFLATED)
      for dirpath, dirnames, filenames in os.walk(temppath):
          fpath = dirpath.replace(temppath, '')  # 不replace的话，就从根目录开始复制
          fpath = fpath and fpath + os.sep or ''
          for filename in filenames:
              z.write(os.path.join(dirpath, filename), fpath + filename)

      #删除文件夹
      import shutil
      shutil.rmtree(temppath)
      #复制一份文件到指定目录下
      #shutil.copy2(ysPath, slicer.modules.recentfile.widgetRepresentation().self().FilePath)
    self.ui.SaveTip.setText('保存已完成')

    #png->pdf
    def PNG_PDF(self,png,pdf_path):
      #安装reportlab之后可以使用
      from reportlab.lib.pagesizes import portrait
      from reportlab.pdfgen import canvas
      from PIL import Image
      (w, h) = Image.open(png).size
      user = canvas.Canvas(pdf_path, pagesize=portrait((w, h)))
      user.drawImage(png, 0, 0, w, h)
      user.showPage()
      user.save()
  #----------------------导航-------------------------------------------
  def delectImageGraph(self):
    try:
      self.p1.clear()
      self.p1.close()
      self.p1.deleteLater()

      self.l1.clear()
      self.l1.deleteLater()

      self.l2.clear()
      self.l2.deleteLater()

      self.fill1.clear()
      self.fill1.deleteLater()

      self.fill2.clear()
      self.fill2.deleteLater()

      self.xian1.clear()
      self.xian1.deleteLater()

      self.xian2.clear()
      self.xian2.deleteLater()

      self.text3.deleteLater()
      self.text4.deleteLater()
      
      self.plotcurves.clear()
      self.curvePoints.clear()
      self.texts.clear()


      print("删除完了")
    
    except Exception as e:
      print(e)
      print("没删除")

  def onNavigationSwitch(self):
    #图片widget
    self.delectImageGraph()
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
    self.ThreeDViewAndImageWidget(self.SwitchState)
    if self.SwitchState == 0:
      self.SwitchState = 1
    elif self.SwitchState == 1:
      self.SwitchState = 2
    elif self.SwitchState == 2:            
      self.SwitchState = 0

  # def DeletAndTransNodeInGuid(self):
  #   transformNode = slicer.util.getNode('变换')
  #   trans = slicer.util.arrayFromTransformMatrix(transformNode)
  #   transformNode1 = slicer.util.getNode('变换_1')
  #   trans1 = slicer.util.arrayFromTransformMatrix(transformNode1)
  #   transformNodeTmp = slicer.util.getNode('变换_临时')
  #   transTmp = slicer.util.arrayFromTransformMatrix(transformNodeTmp)
  #   transformNode2 = slicer.util.getNode('变换_2')
  #   trans2 = slicer.util.arrayFromTransformMatrix(transformNode2)
  #   transformNodeR = slicer.util.getNode('变换_R')
  #   transR = slicer.util.arrayFromTransformMatrix(transformNodeR)
  #   # 胫骨变换
  #   transformNode3 = slicer.util.getNode('变换_3')
  #   trans3 = slicer.util.arrayFromTransformMatrix(transformNode3)
  #   transformNode4 = slicer.util.getNode('变换_4')
  #   trans4 = slicer.util.arrayFromTransformMatrix(transformNode4)
  #   transformNodeTib = slicer.util.getNode('变换_胫骨')
  #   transTib = slicer.util.arrayFromTransformMatrix(transformNodeTib)
  #   transformNode5 = slicer.util.getNode('变换_5')
  #   trans5 = slicer.util.arrayFromTransformMatrix(transformNode5)
  #   transformNodeYueShu = slicer.util.getNode('变换_约束')
  #   transYueShu = slicer.util.arrayFromTransformMatrix(transformNodeYueShu)

  #   # 股骨变换相乘
  #   FemurTrans = np.dot(np.dot(np.dot(np.dot(trans, trans1), transTmp), trans2), transR)
  #   # 胫骨变换相乘
  #   TibiaTrans = np.dot(np.dot(np.dot(np.dot(trans3, trans4), transTib), trans5), transYueShu)
  #   Ttransform6 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'FemurTrans')
  #   Ttransform6.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
  #   transformNode_Femur = slicer.util.getNode('DianjiToTracker1')
  #   Ttransform6.SetAndObserveTransformNodeID(transformNode_Femur.GetID())
  #   slicer.util.getNode(self.jiatiload.GetName()).SetAndObserveTransformNodeID(Ttransform6.GetID())

  #   Ttransform7 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", 'TibiaTrans')
  #   Ttransform7.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(TibiaTrans))
  #   transformNode_Tibia = slicer.util.getNode('TibiaToTracker')
  #   Ttransform7.SetAndObserveTransformNodeID(transformNode_Tibia.GetID())
  #   slicer.util.getNode(self.TibiaJiaTiload.GetName()).SetAndObserveTransformNodeID(Ttransform6.GetID())

  #   self.DeleteNode('变换')
  #   self.DeleteNode('变换_1')
  #   self.DeleteNode('变换_2')
  #   self.DeleteNode('变换_临时')
  #   self.DeleteNode('变换_R')
  #   self.DeleteNode('股骨远端切割')
  #   self.DeleteNode('股骨第一截骨面')
  #   self.DeleteNode('股骨第二截骨面')
  #   self.DeleteNode('股骨第三截骨面')
  #   self.DeleteNode('切割1')
  #   self.DeleteNode('切割2')
  #   self.DeleteNode('切割3')
  #   self.DeleteNode('切割4')
  #   self.DeleteNode('切割5')
  #   self.DeleteNode('部件1')
  #   self.DeleteNode('部件2')
  #   self.DeleteNode('部件3')
  #   self.DeleteNode('部件4')
  #   self.DeleteNode('部件5')
  #   self.DeleteNode('变换_3')
  #   self.DeleteNode('变换_4')
  #   self.DeleteNode('变换_5')
  #   self.DeleteNode('变换_胫骨')
  #   self.DeleteNode('变换_约束')
  #   self.DeleteNode('胫骨近端切割')
  #   self.DeleteNode('胫骨截骨面')
  #   self.DeleteNode('部件6')



  # def SendAngleMessegByPC(self, angle1,angle2,gngle3):
  #   s1 = 2
  #   s2 = 0
  #   s3 = 0
  #   s4 = 0
  #   s5 = 0
  #   s6 =angle1
  #   s7 = angle2
  #   s8 = str(gngle3)+'@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   print(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   self.CurrentTimes = [s1, s2]


  # # 电机校准
  # def onDriveJZ(self):
  #   self.NavigationButtonChecked(self.ui.DriveJZ)
  #   self.HideAll()
  #   self.ui.NavigationWidget.setVisible(True)
  #   self.ui.DriveJZWidget.setVisible(True)

  # # 股骨切割
  # def onFemurQG(self):
  #   self.NavigationButtonChecked(self.ui.FemurQG)
  #   self.HideAll()
  #   self.ui.NavigationWidget.setVisible(True)
  #   self.ui.FemurQGWidget.setVisible(True)
  #   self.YLEnabled(self.ui.FirstPreview)
  #   self.QGEnabled(self.ui.FirstQG)

  # # 胫骨切割
  # def onTibiaQG(self):
  #   self.NavigationButtonChecked(self.ui.TibiaQG)
  #   self.HideAll()
  #   self.ui.NavigationWidget.setVisible(True)

  # ###########################################电机自校准#######################################################################################################
  # def normal(self, a):
  #   # self.isplane()  # 获得该平面的法向量前提是能构成平面
  #   A = a[0]
  #   B = a[1]
  #   C = a[2]  # 对应三个点
  #   AB = [B[0] - A[0], B[1] - A[1], B[2] - A[2]]  # 向量AB
  #   AC = [C[0] - A[0], C[1] - A[1], C[2] - A[2]]  # 向量AC
  #   B1 = AB[0]
  #   B2 = AB[1]
  #   B3 = AB[2]  # 向量AB的xyz坐标
  #   C1 = AC[0]
  #   C2 = AC[1]
  #   C3 = AC[2]  # 向量AC的xyz坐标
  #   n = [B2 * C3 - C2 * B3, B3 * C1 - C3 * B1, B1 * C2 - C1 * B2]  # 已知该平面的两个向量,求该平面的法向量的叉乘公式
  #   return n

  # def GetMarix_y(self, jd):
  #   jd = math.radians(jd)
  #   Tjxlx = [0, 1, 0]
  #   xzjz = np.array([[math.cos(jd) + Tjxlx[0] * Tjxlx[0] * (1 - math.cos(jd)),
  #                     -Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
  #                     Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)), 0],
  #                    [Tjxlx[2] * math.sin(jd) + Tjxlx[0] * Tjxlx[1] * (1 - math.cos(jd)),
  #                     math.cos(jd) + Tjxlx[1] * Tjxlx[1] * (1 - math.cos(jd)),
  #                     -Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)), 0],
  #                    [-Tjxlx[1] * math.sin(jd) + Tjxlx[0] * Tjxlx[2] * (1 - math.cos(jd)),
  #                     Tjxlx[0] * math.sin(jd) + Tjxlx[1] * Tjxlx[2] * (1 - math.cos(jd)),
  #                     math.cos(jd) + Tjxlx[2] * Tjxlx[2] * (1 - math.cos(jd)), 0],
  #                    [0, 0, 0, 1]])
  #   return xzjz



  # def getCrossPointByLine(self, n1, p1, n2, p2):
  #   point1 = p1
  #   point2 = [n1[0] + p1[0], n1[1] + p1[1], n1[2] + p1[2]]
  #   point3 = p2
  #   point4 = [n2[0] + p2[0], n2[1] + p2[1], n2[2] + p2[2]]
  #   epsilon = 0.00000001
  #   L1P0 = np.array([point1[0], point1[1], point1[2]])  # position of P0 on first line
  #   L2P0 = np.array([point3[0], point3[1], point3[2]])  # position of P0 on first line
  #   L1P1 = np.array([point2[0], point2[1], point2[2]])  # ubeam,vbeam and wbeam are direction cosines
  #   L2P1 = np.array([point4[0], point4[1], point4[2]])  # cx,cy,cz are direction cosines
  #   u = L1P1 - L1P0
  #   v = L2P1 - L2P0
  #   w = L1P0 - L2P0
  #   a = np.dot(u, u)
  #   b = np.dot(u, v)
  #   c = np.dot(v, v)
  #   d = np.dot(u, w)
  #   e = np.dot(v, w)
  #   D = a * c - b * b
  #   if D < epsilon:
  #     sc = 0.0
  #     tc = d / b if b > c else e / c
  #   else:
  #     sc = (b * e - c * d) / D
  #     tc = (a * e - b * d) / D
  #   dP = w + (sc * u) - (tc * v)
  #   ClosestPointAtFirst = L1P0 + sc * u
  #   ClosestPointAtSecond = L2P0 + tc * v
  #   pointN1 = (ClosestPointAtSecond + ClosestPointAtFirst) / 2
  #   return pointN1

  # def caculate_mian(self, P):
  #   # 平面拟合，将半圆的Z值变为0，只取X，y拟合计算圆心
  #   F1 = slicer.util.getNode(P)
  #   p3 = slicer.util.arrayFromMarkupsControlPoints(F1)
  #   x = p3[:, 0]
  #   y = p3[:, 1]
  #   z = p3[:, 2]
  #   A = np.ones((len(x), 3))
  #   for i in range(0, len(x)):
  #     A[i, 0] = x[i]
  #     A[i, 1] = y[i]
  #   # print(A)
  #   # 创建矩阵b
  #   b = np.zeros((len(x), 1))
  #   for i in range(0, len(x)):
  #     b[i, 0] = z[i]
  #   # 通过X=(AT*A)-1*AT*b直接求解
  #   A_T = A.T
  #   A1 = np.dot(A_T, A)
  #   A2 = np.linalg.inv(A1)
  #   A3 = np.dot(A2, A_T)
  #   X = np.dot(A3, b)
  #   n = [X[0, 0], X[1, 0], -1]
  #   jxlz = n
  #   moz = np.sqrt(np.square(jxlz[0]) + np.square(jxlz[1]) + np.square(jxlz[2]))  # 基向量x的模
  #   for i in range(0, 3):
  #     jxlz[i] = -jxlz[i] / moz
  #   p_f = np.array([np.average(x[0:10]), np.average(y[0:10]), np.average(z[0:10])])
  #   p_n = np.array([np.average(x[-10:-1]), np.average(y[-10:-1]), np.average(z[-10:-1])])
  #   jxlx = p_n - p_f
  #   mox = np.sqrt(np.square(jxlx[0]) + np.square(jxlx[1]) + np.square(jxlx[2]))  # 基向量x的模
  #   for i in range(0, 3):
  #     jxlx[i] = -jxlx[i] / mox
  #   jxly = [0, 0, 0]  # y轴基向量
  #   jxly[0] = -(jxlx[1] * jxlz[2] - jxlx[2] * jxlz[1])
  #   jxly[1] = -(jxlx[2] * jxlz[0] - jxlx[0] * jxlz[2])
  #   jxly[2] = -(jxlx[0] * jxlz[1] - jxlx[1] * jxlz[0])
  #   moy = np.sqrt(np.square(jxly[0]) + np.square(jxly[1]) + np.square(jxly[2]))  # 基向量x的模
  #   for i in range(0, 3):
  #     jxly[i] = -jxly[i] / moy
  #   zb2 = p_f
  #   trans1 = np.array([[float(jxlx[0]), float(jxly[0]), float(jxlz[0]), zb2[0]],
  #                      [float(jxlx[1]), float(jxly[1]), float(jxlz[1]), zb2[1]],
  #                      [float(jxlx[2]), float(jxly[2]), float(jxlz[2]), zb2[2]],
  #                      [0, 0, 0, 1]])
  #   trans1_ni = np.linalg.inv(trans1)
  #   x = []
  #   y = []
  #   for i in range(0, len(p3)):
  #     tmp = [p3[i][0], p3[i][1], p3[i][2], 1]
  #     x.append(np.dot(trans1_ni, tmp)[0])
  #     y.append(np.dot(trans1_ni, tmp)[1])
  #   # 圆心估计
  #   x_m = np.mean(x)
  #   y_m = np.mean(y)

  #   def calc_R(xc, yc):
  #     """ 计算数据点据圆心(xc, yc)的距离 """
  #     return np.sqrt((x - xc) ** 2 + (y - yc) ** 2)

  #   from scipy import odr
  #   def f_3b(beta, x):
  #     """ implicit definition of the circle """
  #     return (x[0] - beta[0]) ** 2 + (x[1] - beta[1]) ** 2 - beta[2] ** 2

  #   def jacb(beta, x):
  #     """ Jacobian function with respect to the parameters beta.
  #     return df_3b/dbeta
  #     """
  #     xc, yc, r = beta
  #     xi, yi = x
  #     df_db = np.empty((beta.size, x.shape[1]))
  #     df_db[0] = 2 * (xc - xi)  # d_f/dxc
  #     df_db[1] = 2 * (yc - yi)  # d_f/dyc
  #     df_db[2] = -2 * r  # d_f/dr
  #     return df_db

  #   def jacd(beta, x):
  #     """ Jacobian function with respect to the input x.
  #     return df_3b/dx
  #     """
  #     xc, yc, r = beta
  #     xi, yi = x
  #     df_dx = np.empty_like(x)
  #     df_dx[0] = 2 * (xi - xc)  # d_f/dxi
  #     df_dx[1] = 2 * (yi - yc)  # d_f/dyi
  #     return df_dx

  #   def calc_estimate(data):
  #     """ Return a first estimation on the parameter from the data  """
  #     xc0, yc0 = data.x.mean(axis=1)
  #     r0 = np.sqrt((data.x[0] - xc0) ** 2 + (data.x[1] - yc0) ** 2).mean()
  #     return xc0, yc0, r0

  #   # for implicit function :
  #   #       data.x contains both coordinates of the points
  #   #       data.y is the dimensionality of the response
  #   lsc_data = odr.Data(np.row_stack([x, y]), y=1)
  #   lsc_model = odr.Model(f_3b, implicit=True, estimate=calc_estimate, fjacd=jacd, fjacb=jacb)
  #   lsc_odr = odr.ODR(lsc_data, lsc_model)  # beta0 has been replaced by an estimate function
  #   lsc_odr.set_job(deriv=3)  # use user derivatives function without checking
  #   lsc_odr.set_iprint(iter=1, iter_step=1)  # print details for each iteration
  #   lsc_out = lsc_odr.run()

  #   xc_3b, yc_3b, R_3b = lsc_out.beta
  #   Ri_3b = calc_R(xc_3b, yc_3b)
  #   residu_3b = sum((Ri_3b - R_3b) ** 2)
  #   center = [xc_3b, yc_3b, 0, 1]
  #   center1 = np.dot(trans1, center)
  #   F1.RemoveAllControlPoints()
  #   # F1.AddFiducial(center1[0], center1[1], center1[2])
  #   n = [X[0, 0], X[1, 0], -1]
  #   p = center1[0:3]
  #   return n, p

  # def onDJ1Move(self):

  #   dj1 = [0, -90, 90, 0]
  #   self.ifRecv_data1 = 0
  #   for n in range(1, 4):
  #     self.ifRecv_data1 = 0
  #     s1 = 2
  #     s2 = 0
  #     s3 = 0
  #     s4 = 0
  #     s5 = 0
  #     s6 = dj1[n]
  #     s7 = 0
  #     s8 = '0@\n'
  #     self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #     while not self.ifRecv_data1:
  #       time.sleep(0.2)



  # def onDJ2Move(self):
  #   dj1 = [0, -90, 90, 0]
  #   for n in range(1, 4):
  #     self.ifRecv_data1 = 0
  #     s1 = 2
  #     s2 = 0
  #     s3 = 0
  #     s4 = 0
  #     s5 = 0
  #     s6 = 0
  #     s7 = dj1[n]
  #     s8 = '0@\n'
  #     self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #     while not self.ifRecv_data1:
  #       time.sleep(0.2)

  # def onDJ3Move(self):
  #   dj1 = [0, -90, 90, 0]
  #   for n in range(1, 4):
  #     self.ifRecv_data1 = 0
  #     s1 = 2
  #     s2 = 0
  #     s3 = 0
  #     s4 = 0
  #     s5 = 0
  #     s6 = 0
  #     s7 = 0
  #     s8 = str(dj1[n])+'@\n'
  #     self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #     while not self.ifRecv_data1:
  #       time.sleep(0.2)

  # def onTool1(self, unusedArg1=None, unusedArg2=None, unusedArg3=None):
  #   F1 = slicer.util.getNode('DJ-F')
  #   F1.GetDisplayNode().SetTextScale(0)
  #   point1 = [0, 0, 0]
  #   slicer.util.getNode('target').GetNthControlPointPositionWorld(0, point1)
  #   F1.AddFiducial(point1[0], point1[1], point1[2])

  # def getAxisBase(self, xly, xlx, yuandian):
  #   jxly = xly
  #   moy = np.sqrt(np.square(jxly[0]) + np.square(jxly[1]) + np.square(jxly[2]))  # 基向量x的模
  #   for i in range(0, 3):
  #     jxly[i] = -jxly[i] / moy
  #   jxlx = xlx
  #   mox = np.sqrt(np.square(jxlx[0]) + np.square(jxlx[1]) + np.square(jxlx[2]))  # 基向量x的模
  #   for i in range(0, 3):
  #     jxlx[i] = -jxlx[i] / mox
  #   jxlz = [0, 0, 0]  # y轴基向量
  #   jxlz[0] = -(jxlx[1] * jxly[2] - jxlx[2] * jxly[1])
  #   jxlz[1] = -(jxlx[2] * jxly[0] - jxlx[0] * jxly[2])
  #   jxlz[2] = -(jxlx[0] * jxly[1] - jxlx[1] * jxly[0])
  #   moz = np.sqrt(np.square(jxlz[0]) + np.square(jxlz[1]) + np.square(jxlz[2]))  # 基向量x的模
  #   for i in range(0, 3):
  #     jxlz[i] = -jxlz[i] / moz
  #   trans1 = np.array([[float(jxlx[0]), float(jxly[0]), float(jxlz[0]), yuandian[0]],
  #                      [float(jxlx[1]), float(jxly[1]), float(jxlz[1]), yuandian[1]],
  #                      [float(jxlx[2]), float(jxly[2]), float(jxlz[2]), yuandian[2]],
  #                      [0, 0, 0, 1]])
  #   return trans1

  # def Startjiaozhun(self):
  #   Knife = slicer.util.getNode("KnifeToTracker")
  #   self.Observer_Knife = Knife.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTool1)
  #   self.F = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'DJ-F')
  #   self.onDJ1Move()
  #   Knife.RemoveObserver(self.Observer_Knife)
  #   p3 = slicer.util.arrayFromMarkupsControlPoints(self.F)
  #   print("p3", p3)
  #   n1, p1 = self.caculate_mian("DJ-F")
  #   self.Observer_Knife = Knife.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTool1)
  #   self.onDJ2Move()
  #   Knife.RemoveObserver(self.Observer_Knife)
  #   p3 = slicer.util.arrayFromMarkupsControlPoints(self.F)
  #   print("p3", p3)
  #   n2, p2 = self.caculate_mian("DJ-F")
  #   axisPoint1 = self.getCrossPointByLine(n1, p1, n2, p2)
  #   F1 = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'axisPoint1')
  #   F1.AddFiducial(axisPoint1[0], axisPoint1[1], axisPoint1[2])
  #   self.Observer_Knife = Knife.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, self.onTool1)
  #   self.onDJ3Move()
  #   Knife.RemoveObserver(self.Observer_Knife)
  #   n3, p3 = self.caculate_mian("DJ-F")
  #   axisPoint2 = self.getCrossPointByLine(n2, p2, n3, p3)
  #   F2 = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'axisPoint2')
  #   F2.AddFiducial(axisPoint2[0], axisPoint2[1], axisPoint2[2])
  #   # print("角度",self.Angle(n1,n3))
  #   trans = self.getAxisBase(axisPoint1 - p1, p2 - axisPoint1, axisPoint1)
  #   self.RASToDJTrans=np.linalg.inv(trans)
  #   #tannode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', 'trans')
  #   #tannode.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans_ni))


  # def onOpenDjShineng(self):
  #   if(self.ui.pushButton_openDj.checked):
  #     s1 = 2
  #     s2 = 1
  #     s3 = 1
  #     s4 = 0
  #     s5 = 0
  #     s6 = 0
  #     s7 = 0
  #     s8 = '0@\n'
  #   else:
  #     s1 = 2
  #     s2 = 1
  #     s3 = 0
  #     s4 = 0
  #     s5 = 0
  #     s6 = 0
  #     s7 = 0
  #     s8 = '0@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())



  # def caculateFiveAngle(self):
  #   # 计算原理：
  #   # 需求为根据所给目标平面，计算出三轴机械臂每个电机的角度，以让切割平面与目标平面重合。
  #   # 已知条件为目标平面及当前电机位置，最后一个旋转轴也在切割平面上。
  #   # 取旋转轴上两点，一点为第一个旋转轴与该轴交点（为第二个机械臂的原点p1（0，0，0）），
  #   # 该点仅受第一个电机旋转影响，坐标为dj1*dj2_position*p1（dj1为绕y轴旋转矩阵）
  #   # 另一点为该坐标系上p2（0，50，0）
  #   # 该点受第一个电机旋转影响，及第二个电机旋转影响，坐标为dj1*dj2_position*dj2*p2
  #   # 将第一个坐标带入目标平面方程，可得出电机1旋转角度
  #   # 将第二个坐标及电机1旋转角度带入目标平面方程，可得出电机2旋转角度
  #   # 第三个电机旋转角度，计算出当前（旋转了电机1、2后）p2的世界坐标，p3(最后一个臂延长线上一点，（-50,50,0,1）)世界坐标，
  #   # 求P3在目标平面投影点，则第三个角度大小为投影点，P2，p3角度，方向未知
  #   # 方向计算是再旋转第三刀，得出p3当前位置，看看正负角度下哪个更近，哪个就是正确的
  #   # 存储每一刀每个电机的位置（绝对角度）


  #   if self.jiatiload.GetName() == 'femur-R1-5' or self.jiatiload.GetName() == 'femur-l1-5':
  #     FemurJieGu = np.array([[2.55354824e+01, -8.14475775e-01, -1.89999994e-02],
  #                           [-2.53006878e+01, 3.83428359e+00, -1.89999994e-02],
  #                           [-2.48460236e+01, -3.59935689e+00, -1.89999994e-02],
  #                           [2.16231194e+01, -2.31011543e+01, 2.25814362e+01],
  #                           [4.11882496e+00, -2.40347691e+01, 3.13389416e+01],
  #                           [-1.65763512e+01, -2.26524277e+01, 1.83728542e+01],
  #                           [2.77351227e+01, 1.59605360e+01, 9.65126419e+00],
  #                           [1.71729660e+01, 1.61901855e+01, 2.26250839e+01],
  #                           [-2.74971828e+01, 1.60632057e+01, 1.54485464e+01],
  #                           [2.75983887e+01, 1.05208902e+01, 1.39612436e+00],
  #                           [1.17515240e+01, 1.48522539e+01, 5.66603804e+00],
  #                           [-2.74415989e+01, 1.05128107e+01, 1.38815999e+00],
  #                           [2.40934410e+01, -2.04364090e+01, 1.12611094e+01],
  #                           [1.17380333e+01, -1.08793507e+01, 1.83952510e+00],
  #                           [-2.00051403e+01, -2.01736851e+01, 1.10021296e+01]])

  #   elif self.jiatiload.GetName() == 'femur-R2' or self.jiatiload.GetName() == 'femur-l2':
  #     FemurJieGu = np.array([[2.62008972e+01, -7.70488679e-01, -2.00999994e-02],
  #                            [-2.71445332e+01, 3.02385926e+00, -2.00999994e-02],
  #                            [-2.73737278e+01, -3.76405716e+00, -2.00999994e-02],
  #                            [2.21813183e+01, -2.43905201e+01, 2.26475849e+01],
  #                            [3.30812049e+00, -2.53597298e+01, 3.17385426e+01],
  #                            [-1.77289200e+01, -2.39305611e+01, 1.83335438e+01],
  #                            [2.85430222e+01, 1.76676655e+01, 9.80583286e+00],
  #                            [1.85107498e+01, 1.79083366e+01, 2.33955517e+01],
  #                            [-2.91739674e+01, 1.77374706e+01, 1.37461853e+01],
  #                            [2.87510014e+01, 1.21107759e+01, 2.46474528e+00],
  #                            [1.14945717e+01, 1.59459496e+01, 6.24556208e+00],
  #                            [-2.90054836e+01, 1.29157162e+01, 3.25828624e+00],
  #                            [2.45252018e+01, -2.05777683e+01, 1.08956213e+01],
  #                            [1.14454269e+01, -1.19923363e+01, 2.43196177e+00],
  #                            [-2.15349503e+01, -2.03837528e+01, 1.07043695e+01]])

  #   elif self.jiatiload.GetName() == 'femur-R2-5' or self.jiatiload.GetName() == 'femur-l2-5':
  #     FemurJieGu = np.array([[2.62008972e+01, -7.70488679e-01, -2.00999994e-02],
  #                            [-2.71445332e+01, 3.02385926e+00, -2.00999994e-02],
  #                            [-2.73737278e+01, -3.76405716e+00, -2.00999994e-02],
  #                            [2.43205681e+01, -2.60973759e+01, 2.36747284e+01],
  #                            [2.51188397e+00, -2.72616959e+01, 3.45956383e+01],
  #                            [-1.91332684e+01, -2.56864700e+01, 1.98200054e+01],
  #                            [3.01704578e+01, 1.84891891e+01, 1.12920475e+01],
  #                            [1.96298065e+01, 1.87163734e+01, 2.41217976e+01],
  #                            [-3.07903404e+01, 1.85243053e+01, 1.32740393e+01],
  #                            [3.01063328e+01, 1.18808479e+01, 1.52185678e+00],
  #                            [1.16542416e+01, 1.66802406e+01, 6.25324202e+00],
  #                            [-3.07861137e+01, 1.30809269e+01, 2.70493031e+00],
  #                            [2.65876884e+01, -2.08674088e+01, 1.04918737e+01],
  #                            [1.17710781e+01, -1.37550602e+01, 3.48031425e+00],
  #                            [-2.34589748e+01, -2.06486568e+01, 1.02762098e+01]])

  #   elif self.jiatiload.GetName() == 'femur-R3' or self.jiatiload.GetName() == 'femur-l3':
  #     FemurJieGu = np.array([[2.62008972e+01, -7.70488679e-01, -2.00999994e-02],
  #                            [-2.71445332e+01, 3.02385926e+00, -2.00999994e-02],
  #                            [-2.73737278e+01, -3.76405716e+00, -2.00999994e-02],
  #                            [2.48561649e+01, -2.79111748e+01, 2.43407154e+01],
  #                            [2.06988120e+00, -2.92271366e+01, 3.66839066e+01],
  #                            [-1.92885361e+01, -2.74815102e+01, 2.03108711e+01],
  #                            [3.18946171e+01, 1.94151878e+01, 1.15617962e+01],
  #                            [2.26744308e+01, 1.96965675e+01, 2.74523563e+01],
  #                            [-3.17952747e+01, 1.94693222e+01, 1.46191893e+01],
  #                            [3.20082970e+01, 1.28028412e+01, 1.52113855e+00],
  #                            [1.17890978e+01, 1.62057762e+01, 4.87585354e+00],
  #                            [-3.20670357e+01, 1.36194630e+01, 2.32618904e+00],
  #                            [2.82055321e+01, -2.11564445e+01, 9.88112259e+00],
  #                            [1.17145710e+01, -1.42333670e+01, 3.05618310e+00],
  #                            [-2.42979164e+01, -2.02131824e+01, 8.95121288e+00]])

  #   elif self.jiatiload.GetName() == 'femur-R4' or self.jiatiload.GetName() == 'femur-l4':
  #     FemurJieGu = np.array([[2.62008972e+01, -7.70488679e-01, -2.00999994e-02],
  #                            [-2.71445332e+01, 3.02385926e+00, -2.00999994e-02],
  #                            [-2.73737278e+01, -3.76405716e+00, -2.00999994e-02],
  #                            [2.71135921e+01, -3.00985260e+01, 2.39664307e+01],
  #                            [1.36029232e+00, -3.18115063e+01, 4.00334320e+01],
  #                            [-2.05988426e+01, -2.98338966e+01, 2.14843445e+01],
  #                            [3.42298965e+01, 2.09348717e+01, 1.21202650e+01],
  #                            [1.97166481e+01, 2.12379608e+01, 2.92334518e+01],
  #                            [-3.49024086e+01, 2.09894943e+01, 1.52036381e+01],
  #                            [3.41674919e+01, 1.46932631e+01, 2.17265892e+00],
  #                            [1.17235880e+01, 1.60913620e+01, 3.55094218e+00],
  #                            [-3.47100334e+01, 1.54675999e+01, 2.93602061e+00],
  #                            [3.08363819e+01, -2.11723690e+01, 8.70182610e+00],
  #                            [1.21058197e+01, -1.76750832e+01, 5.25406885e+00],
  #                            [-2.68051319e+01, -2.06128502e+01, 8.15026188e+00]])

  #   elif self.jiatiload.GetName() == 'femur-R5' or self.jiatiload.GetName() == 'femur-l5':
  #     FemurJieGu = np.array([[2.62008972e+01, -7.70488679e-01, -2.00999994e-02],
  #                            [-2.71445332e+01, 3.02385926e+00, -2.00999994e-02],
  #                            [-2.73737278e+01, -3.76405716e+00, -2.00999994e-02],
  #                            [2.79475822e+01, -3.06654434e+01, 2.49838390e+01],
  #                            [4.14048195e+00, -3.27869606e+01, 4.48823128e+01],
  #                            [-2.06827507e+01, -3.05231037e+01, 2.36487217e+01],
  #                            [3.54963760e+01, 2.31229362e+01, 1.44909897e+01],
  #                            [1.86421375e+01, 2.34105682e+01, 3.07393436e+01],
  #                            [-3.56858444e+01, 2.31387405e+01, 1.53860674e+01],
  #                            [3.53801308e+01, 1.40798883e+01, 2.26884556e+00],
  #                            [1.23895378e+01, 1.67398891e+01, 4.89115429e+00],
  #                            [-3.55210419e+01, 1.52589035e+01, 3.43114781e+00],
  #                            [3.12312393e+01, -2.13347435e+01, 9.56075954e+00],
  #                            [1.21865911e+01, -1.85200424e+01, 6.78594971e+00],
  #                            [-2.76725655e+01, -2.06865768e+01, 8.92174816e+00]])

  #   self.dj1_pisitions = []
  #   self.dj2_pisitions = []
  #   self.dj3_pisitions = []
  #   # 设置角度的未知数x，以对x进行求解
  #   x = sympy.Symbol('x')
  #   transNode1 = slicer.util.getNode("DianjiToTracker1")
  #   trans1 = slicer.util.arrayFromTransformMatrix(transNode1)
  #   transNode2=slicer.util.getNode("FemurTrans")
  #   trans2 = slicer.util.arrayFromTransformMatrix(transNode2)
  #   trans3=np.dot(trans1,trans2)
  #   for i in range(5):
  #     point1=FemurJieGu[i*3]
  #     point2=FemurJieGu[i*3+1]
  #     point3=FemurJieGu[i*3+2]
  #     plane1 = np.array([[point1[0], point1[1], point1[2], 1],
  #                        [point2[0], point2[1], point2[2], 1],
  #                        [point3[0], point3[1], point3[2], 1]])
  #     for j in range(3):
  #       plane1[j] = np.dot(trans3, plane1[j])

  #     plane = np.empty([3, 3])
  #     for j in range(3):
  #       plane[j] = np.dot(self.RASToDJTrans, plane1[j])[0:3]
  #     # 根据三个点获取目标平面方程的参数
  #     A, B, C, D = self.define_area(plane)
  #     # 方程一，求解角度1（115.2为电机2的原点相对电机1的原点移动位置，dj2_position矩阵中的x值）
  #     fx = -115.2 * sympy.cos(x) * A + 115.2 * sympy.sin(x) * C + D
  #     angel1_degs = sympy.solve(fx, x)
  #     if (len(angel1_degs) > 1):
  #       if (abs(math.degrees(angel1_degs[0])) < abs(math.degrees(angel1_degs[1]))):
  #         angel1_deg = angel1_degs[0]
  #         selectIndex = 0
  #       else:
  #         angel1_deg = angel1_degs[1]
  #         selectIndex = 1
  #       angle1 = math.degrees(angel1_deg)
  #       # 第二及第三刀，第一个电机需要一个正值
  #       if (i == 1 or i == 2):
  #         if (angle1 < 0):
  #           angel1_deg = angel1_degs[1 - selectIndex]
  #           angle1 = math.degrees(angel1_deg)
  #     else:
  #       angel1_deg = sympy.nsolve(fx, 0)
  #       angle1 = math.degrees(angel1_deg)
  #     # 方程二，求解角度2
  #     fx = (50 * sympy.sin(angel1_deg) * sympy.sin(x) - 115.2 * sympy.cos(angel1_deg)) * A + (50 * sympy.cos(x)) * B + (
  #               50 * sympy.cos(angel1_deg) * sympy.sin(x) + 115.2 * sympy.sin(angel1_deg)) * C + D
  #     angle2_degs = sympy.solve(fx, x)
  #     if (len(angle2_degs) > 1):
  #       if (abs(math.degrees(angle2_degs[0])) < abs(math.degrees(angle2_degs[1]))):
  #         angle2_deg = angle2_degs[0]
  #       else:
  #         angle2_deg = angle2_degs[1]
  #       angle2 = math.degrees(angle2_deg)
  #     else:
  #       angle2_deg = sympy.nsolve(fx, 0)
  #       angle2 = math.degrees(angle2_deg)
  #     # 第三个电机旋转角度，计算出当前（旋转了电机1、2后）p2的世界坐标（dj3_position）
  #     dj3_position = [50.0 * sympy.sin(angel1_deg) * sympy.sin(angle2_deg) - 115.2 * sympy.cos(angel1_deg),
  #                     50.0 * sympy.cos(angle2_deg),
  #                     50.0 * sympy.cos(angel1_deg) * sympy.sin(angle2_deg) + 115.2 * sympy.sin(angel1_deg)]
  #     # p3(最后一个臂延长线上一点)世界坐标，lastPoint
  #     lastPoint = [
  #       -50.0 * sympy.cos(angel1_deg) + 50.0 * sympy.sin(angel1_deg) * sympy.sin(angle2_deg) - 115.2 * sympy.cos(
  #         angel1_deg),
  #       50.0 * sympy.cos(angle2_deg),
  #       50.0 * sympy.sin(angel1_deg) + 50.0 * sympy.cos(angel1_deg) * sympy.sin(angle2_deg) + 115.2 * sympy.sin(
  #         angel1_deg)]
  #     # 求P3在目标平面投影点，
  #     lastPoint_touying = self.TouYing(plane, lastPoint)
  #     N_before = np.array(lastPoint) - np.array(dj3_position)
  #     N_predict = np.array(lastPoint_touying) - np.array(dj3_position)
  #     angle3 = self.Angle(N_before, N_predict)
  #     # 再旋转第三刀，得出p3当前位置
  #     transform0 = self.GetMarix_y(angle1)
  #     transform1 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('dj2_position'))
  #     transform2 = self.GetMarix_x(angle2)
  #     transform3 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('dj3_position'))
  #     transform4 = self.GetMarix_y(angle3)
  #     transform5 = self.GetMarix_y(-angle3)
  #     Trans = np.dot(np.dot(np.dot(np.dot(transform0, transform1), transform2), transform3), transform4)
  #     Trans1 = np.dot(np.dot(np.dot(np.dot(transform0, transform1), transform2), transform3), transform5)
  #     lastPoint_1 = np.dot(Trans, [-50, 50, 0, 1])[0:3]
  #     lastPoint_2 = np.dot(Trans1, [-50, 50, 0, 1])[0:3]
  #     d1 = self.point2area_distance(plane, lastPoint_1)
  #     d2 = self.point2area_distance(plane, lastPoint_2)
  #     if (d2 < d1):
  #       angle3 = -angle3
  #     self.dj1_pisitions.append(angle1)
  #     self.dj2_pisitions.append(angle2)
  #     self.dj3_pisitions.append(angle3)



  # --------------------------切割------------------------------------------
  # 获取点在线上的垂足
  # def getFootPoint(self, point, line_p1, line_p2):
  #   """
  #   @point, line_p1, line_p2 : [x, y, z]
  #   """
  #   x0 = point[0]
  #   y0 = point[1]
  #   z0 = point[2]
  #   x1 = line_p1[0]
  #   y1 = line_p1[1]
  #   z1 = line_p1[2]
  #   x2 = line_p2[0]
  #   y2 = line_p2[1]
  #   z2 = line_p2[2]
  #   k = -((x1 - x0) * (x2 - x1) + (y1 - y0) * (y2 - y1) + (z1 - z0) * (z2 - z1)) / \
  #       ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) * 1.0
  #   xn = k * (x2 - x1) + x1
  #   yn = k * (y2 - y1) + y1
  #   zn = k * (z2 - z1) + z1
  #   p = np.array([xn, yn, zn])
  #   return p


  # # 轨迹预览Enabled
  # def YLEnabled(self, checkBox):
  #   self.ui.FirstPreview.setEnabled(False)
  #   self.ui.SecondPreview.setEnabled(False)
  #   self.ui.ThirdPreview.setEnabled(False)
  #   self.ui.FourthPreview.setEnabled(False)
  #   self.ui.FifthPreview.setEnabled(False)
  #   checkBox.setEnabled(True)
  #   self.setPreviewBoxState(checkBox)

  # def setPreviewBoxState(self, checkBox):
  #   for i in range(0, len(self.ui.PreviewBox.findChildren("QCheckBox"))):
  #     self.ui.PreviewBox.findChildren("QCheckBox")[i].setStyleSheet("None")
  #   checkBox.setStyleSheet("background:#515151;color:#7bcd27;font-weight:bold;")

  # def setQGBoxState(self, checkBox):
  #   for i in range(0, len(self.ui.QGBox.findChildren("QCheckBox"))):
  #     self.ui.QGBox.findChildren("QCheckBox")[i].setStyleSheet("None")
  #   checkBox.setStyleSheet("background:#515151;color:#7bcd27;font-weight:bold;")

  # def onFirstPreview(self):
  #   self.onGetMatrix(1)
  #   self.YLEnabled(self.ui.SecondPreview)

  # def onSecondPreview(self):
  #   self.onGetMatrix(2)
  #   self.YLEnabled(self.ui.ThirdPreview)

  # def onThirdPreview(self):
  #   self.onGetMatrix(3)
  #   self.YLEnabled(self.ui.FourthPreview)

  # def onFourthPreview(self):
  #   self.onGetMatrix(4)
  #   self.YLEnabled(self.ui.FifthPreview)

  # def onFifthPreview(self):
  #   self.onGetMatrix(5)
  #   self.ui.FifthPreview.setEnabled(False)


  # def onPreviewReSet(self):
  #   self.YLChecked(self.ui.PreviewReSet)
  #   dj1xz = slicer.util.getNode('xz1')
  #   dj2xz = slicer.util.getNode('xz2')
  #   dj1xz.SetMatrixTransformToParent(vtk.vtkMatrix4x4())
  #   dj2xz.SetMatrixTransformToParent(vtk.vtkMatrix4x4())
  #   self.YLChecked(self.ui.FirstPreview)
  #   self.ui.FirstPreview.setChecked(False)
  #   self.ui.SecondPreview.setChecked(False)
  #   self.ui.ThirdPreview.setChecked(False)
  #   self.ui.FourthPreview.setChecked(False)
  #   self.ui.FifthPreview.setChecked(False)

  # # 切割setCheckedable
  # def QGEnabled(self, checkBox):
  #   self.ui.FirstQG.setEnabled(False)
  #   self.ui.SecondQG.setEnabled(False)
  #   self.ui.ThirdQG.setEnabled(False)
  #   self.ui.FourthQG.setEnabled(False)
  #   self.ui.FifthQG.setEnabled(False)
  #   checkBox.setEnabled(True)
  #   self.setQGBoxState(checkBox)
  #   self.ViewTip(self.view1)

  # def onFirstQG(self):
  #   s1 = 2
  #   s2 = 0
  #   s3 = 0
  #   s4 = 0
  #   s5 = 0
  #   s6 = self.dj1_pisitions[0]
  #   s7 = self.dj2_pisitions[0]
  #   s8 = str(self.dj3_pisitions[0]) + '@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   self.QGEnabled(self.ui.SecondQG)

  # def onSecondQG(self):
  #   s1 = 2
  #   s2 = 0
  #   s3 = 0
  #   s4 = 0
  #   s5 = 0
  #   s6 = self.dj1_pisitions[1]
  #   s7 = self.dj2_pisitions[1]
  #   s8 = str(self.dj3_pisitions[1]) + '@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   self.QGEnabled(self.ui.ThirdQG)

  # def onThirdQG(self):
  #   s1 = 2
  #   s2 = 0
  #   s3 = 0
  #   s4 = 0
  #   s5 = 0
  #   s6 = self.dj1_pisitions[2]
  #   s7 = self.dj2_pisitions[2]
  #   s8 = str(self.dj3_pisitions[2]) + '@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   self.QGEnabled(self.ui.FourthQG)

  # def onFourthQG(self):
  #   s1 = 2
  #   s2 = 0
  #   s3 = 0
  #   s4 = 0
  #   s5 = 0
  #   s6 = self.dj1_pisitions[3]
  #   s7 = self.dj2_pisitions[3]
  #   s8 = str(self.dj3_pisitions[3]) + '@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   self.QGEnabled(self.ui.FifthQG)

  # def onFifthQG(self):
  #   s1 = 2
  #   s2 = 0
  #   s3 = 0
  #   s4 = 0
  #   s5 = 0
  #   s6 = self.dj1_pisitions[4]
  #   s7 = self.dj2_pisitions[4]
  #   s8 = str(self.dj3_pisitions[4]) + '@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   self.ui.FifthQG.setEnabled(False)

  # def onQGReSet(self):
  #   s1 = 2
  #   s2 = 0
  #   s3 = 0
  #   s4 = 0
  #   s5 = 0
  #   s6 = 0
  #   s7 = 0
  #   s8 = '0@\n'
  #   self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
  #   self.QGEnabled(self.ui.FirstQG)
  #   self.ui.FirstQG.setChecked(False)
  #   self.ui.SecondQG.setChecked(False)
  #   self.ui.ThirdQG.setChecked(False)
  #   self.ui.FourthQG.setChecked(False)
  #   self.ui.FifthQG.setChecked(False)









  # def findPointAxis(self, zuobiao, jd):
  #   import math
  #   juli = 60
  #   x1 = juli * math.cos(math.radians(jd))
  #   y1 = juli * math.sin(math.radians(jd))
  #   zuobiao1 = [0, 0]
  #   zuobiao1[0] = zuobiao[0] - x1
  #   zuobiao1[1] = zuobiao[1] - y1
  #   print(zuobiao1)
  #   return zuobiao1

  # def ViewTip(self, view):
  #   for i in range(0,len(view.findChildren("QLabel"))):
  #     view.findChildren("QLabel")[-1].delete()
  #   V11 = qt.QLabel(view)
  #   V12 = qt.QLabel(view)
  #   V13 = qt.QLabel(view)
  #   V14 = qt.QLabel(view)
  #   V15 = qt.QLabel(view)
  #   V16 = qt.QLabel(view)
  #   V17 = qt.QLabel(view)
  #   V18 = qt.QLabel(view)
  #   V11.setGeometry(view.contentsRect().width() - 100, 25, 100, 25)
  #   V11.setText(" 伸直夹角 ")
  #   V11.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V11.show()
  #   V12.setGeometry(view.contentsRect().width() - 100, 50, 100, 25)
  #   try:
  #     V12.setText(' ' + str(round(self.ShenZhiJiaJiao, 1)) + '°')
  #   except Exception as e:
  #     print(e)
  #   V12.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V12.show()
  #   V13.setGeometry(view.contentsRect().width() - 100, 75, 100, 25)
  #   V13.setText(" 伸直间隙 ")
  #   V13.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V13.show()
  #   V14.setGeometry(view.contentsRect().width() - 100, 100, 100, 25)
  #   try:
  #     V14.setText(' ' + str(round(self.ShenZhiJianXi, 1)) + 'mm')
  #   except Exception as e:
  #     print(e)
  #   V14.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V14.show()
  #   V15.setGeometry(0, 25, 100, 25)
  #   V15.setText(" 屈膝夹角 ")
  #   V15.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V15.show()
  #   V16.setGeometry(0, 50, 100, 25)
  #   try:
  #     V16.setText(' ' + str(round(self.QuXiJiaJiao, 1)) + 'mm')
  #   except Exception as e:
  #     print(e)
  #   V16.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V16.show()
  #   V17.setGeometry(0, 75, 100, 25)
  #   V17.setText(" 屈膝间隙 ")
  #   V17.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V17.show()
  #   V18.setGeometry(0, 100, 100, 25)
  #   try:
  #     V18.setText(' ' + str(round(self.QuXiJianXi, 1)) + 'mm')
  #   except Exception as e:
  #     print(e)
  #   V18.setStyleSheet('QLabel{background-color:transparent;color:#7BCD27;font:15px;}')
  #   V18.show()

  # def CalculationAngle(self):
  #   # 伸直夹角
  #   # 获取世界坐标系下截骨面的坐标矩阵
  #   FJGM = self.GetTransPoint('股骨真实截骨面')
  #   # 胫骨真实截骨面
  #   TJGM = self.GetTransPoint('胫骨电机点列')
  #   # 获取截骨面的法向量
  #   FFXL = self.normal(FJGM)
  #   TFXL = self.normal(TJGM)
  #   self.ShenZhiJiaJiao = self.angle(FFXL, TFXL)
  #   # 屈膝夹角
  #   F3JGM = self.GetTransPoint('股骨第三真实截骨面')
  #   F3FXL = self.normal(F3JGM)
  #   self.QuXiJiaJiao = self.angle(F3FXL, TFXL)

  # def CalculationDistance(self):
  #   # 伸直间隙
  #   point1, point2 = [0, 0, 0], [0, 0, 0]
  #   slicer.util.getNode('股骨真实截骨面').GetNthControlPointPositionWorld(0, point1)
  #   TJGM = self.GetTransPoint('胫骨电机点列')
  #   self.ShenZhiJianXi = self.point2area_distance(TJGM, point1)
  #   # 屈曲间隙
  #   slicer.util.getNode('内侧后髁').GetNthControlPointPositionWorld(0, point2)
  #   F3JGM = self.GetTransPoint('股骨第三真实截骨面')
  #   self.QuXiJianXi = self.point2area_distance(F3JGM, point2)

  # # 判断角度正负
  # def jd1zhengfu(self, point_pre, point_pos):
  #   a = -1
  #   xl1 = np.array([point_pos[0] - point_pre[0], point_pos[1] - point_pre[1]])
  #   xl2 = np.array([0, -1])
  #   if np.dot(xl1, xl2) > 0:
  #     a = 1
  #   return a

  # # 判断这三个点是否能构成平面
  # def isplane(self, a):
  #   coors = [[], [], []]  # 三个点的xyz坐标分别放在同一个列表用来比较
  #   for _point in a:  # 对于每个点
  #     coors[0].append(_point.x)
  #     coors[1].append(_point.y)
  #     coors[2].append(_point.z)
  #   for coor in coors:
  #     if coor[0] == coor[1] == coor[2]:  # 如果三个点的x或y或z坐标相等 则不能构成平面
  #       return print('Points:cannot form a plane')

  # # 获得平面的法向量
  # def normal(self, a):
  #   # self.isplane()  # 获得该平面的法向量前提是能构成平面
  #   A = a[0]
  #   B = a[1]
  #   C = a[2]  # 对应三个点
  #   AB = [B[0] - A[0], B[1] - A[1], B[2] - A[2]]  # 向量AB
  #   AC = [C[0] - A[0], C[1] - A[1], C[2] - A[2]]  # 向量AC
  #   B1 = AB[0]
  #   B2 = AB[1]
  #   B3 = AB[2]  # 向量AB的xyz坐标
  #   C1 = AC[0]
  #   C2 = AC[1]
  #   C3 = AC[2]  # 向量AC的xyz坐标
  #   n = [B2 * C3 - C2 * B3, B3 * C1 - C3 * B1, B1 * C2 - C1 * B2]  # 已知该平面的两个向量,求该平面的法向量的叉乘公式
  #   return n

  # 两个平面的夹角
  def angle(self, P1, P2):
    import math
    x1, y1, z1 = P1  # 该平面的法向量的xyz坐标
    x2, y2, z2 = P2  # 另一个平面的法向量的xyz坐标
    cosθ = ((x1 * x2) + (y1 * y2) + (z1 * z2)) / (
            ((x1 ** 2 + y1 ** 2 + z1 ** 2) ** 0.5) * ((x2 ** 2 + y2 ** 2 + z2 ** 2) ** 0.5))  # 平面向量的二面角公式
    degree = math.degrees(math.acos(cosθ))
    if degree > 90:  # 二面角∈[0°,180°] 但两个平面的夹角∈[0°,90°]
      degree = 180 - degree

    return str(round(degree, 5))

  # 删除节点
  def DeleteNode(self, node):
    try:
      slicer.mrmlScene.RemoveNode(slicer.util.getNode(node))
    except Exception as e:
      print(e)

  # 删除前面创建的所有节点
  def DeleteAllNode(self):
    self.DeleteNode('股骨远端切割')
    self.DeleteNode('DynamicModeler')
    self.DeleteNode('股骨远端')
    self.DeleteNode('切割1')
    self.DeleteNode('切割2')
    self.DeleteNode('切割3')
    self.DeleteNode('切割4')
    self.DeleteNode('切割5')
    self.DeleteNode('部件1')
    self.DeleteNode('部件2')
    self.DeleteNode('部件3')
    self.DeleteNode('部件4')
    self.DeleteNode('部件5')
    self.DeleteNode('动态切割1')
    self.DeleteNode('动态切割2')
    self.DeleteNode('动态切割3')
    self.DeleteNode('动态切割4')
    self.DeleteNode('动态切割5')
    self.DeleteNode('股骨切割')
    self.DeleteNode('胫骨近端切割')
    self.DeleteNode('胫骨近端')
    self.DeleteNode('DynamicModeler_1')
    self.DeleteNode('胫骨切割')
    self.DeleteNode('切割6')
    self.DeleteNode('部件6')
    self.DeleteNode('动态切割6')
    # self.DeleteNode('内侧高点')
    # self.DeleteNode('外侧高点')
    # 将变换相乘 得到股骨变换和胫骨变换
    try:
      transform = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换'))
      transform1 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_1'))
      transform2 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_2'))
      transform3 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_3'))
      transform4 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_4'))
      transform5 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_5'))
      #transform6 = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_6'))
      transform_R = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_R'))
      transform_jg = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_胫骨'))
      transform_ys = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_约束'))
      transform_tmp = slicer.util.arrayFromTransformMatrix(slicer.util.getNode('变换_临时'))
      FemurTrans = np.dot(np.dot(np.dot(np.dot(transform, transform1), transform_tmp), transform2), transform_R)
      TibiaTrans = np.dot(np.dot(np.dot(transform3, transform4), transform_jg), transform_ys)
      FemurTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '股骨假体变换')
      FemurTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(FemurTrans))
      TibiaTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTransformNode", '胫骨假体变换')
      TibiaTransform.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(TibiaTrans))
      self.jiatiload.SetAndObserveTransformNodeID(FemurTransform.GetID())
      slicer.util.getNode(self.TibiaJiaTiload.GetName()).SetAndObserveTransformNodeID(TibiaTransform.GetID())

      transNode1 = slicer.util.getNode('DianjiToTracker1')
      transNode2 = slicer.util.getNode('TibiaToTracker')
      FemurTransform.SetAndObserveTransformNodeID(transNode1.GetID())
      TibiaTransform.SetAndObserveTransformNodeID(transNode2.GetID())

      slicer.util.getNode('Femur').SetAndObserveTransformNodeID(FemurTransform.GetID())
      slicer.util.getNode('Tibia').SetAndObserveTransformNodeID(TibiaTransform.GetID())

    except Exception as e:
      print(e)

    self.DeleteNode('变换')
    self.DeleteNode('变换_1')
    self.DeleteNode('变换_2')
    self.DeleteNode('变换_3')
    self.DeleteNode('变换_4')
    self.DeleteNode('变换_5')
    self.DeleteNode('变换_R')
    self.DeleteNode('变换_胫骨')
    self.DeleteNode('变换_约束')
    self.DeleteNode('变换_临时')
    self.DeleteNode('股骨截骨面')
    self.DeleteNode('股骨第一截骨面')
    self.DeleteNode('股骨第二截骨面')
    self.DeleteNode('股骨第三截骨面')
    self.DeleteNode('胫骨截骨面')
    # self.DeleteNode('股骨头球心')
    # self.DeleteNode('开髓点')
    # self.DeleteNode('H点')
    # self.DeleteNode('A点')
    # self.DeleteNode('外侧远端')
    # self.DeleteNode('内侧远端')
    # self.DeleteNode('外侧皮质高点')
    # self.DeleteNode('外侧后髁')
    # self.DeleteNode('内侧后髁')
    # self.DeleteNode('内侧凹点')
    # self.DeleteNode('外侧凸点')
    # self.DeleteNode('胫骨隆凸')
    # self.DeleteNode('胫骨结节')
    # self.DeleteNode('踝穴中心')
    self.DeleteNode('Femur_ZAxis')
    self.DeleteNode('Femur_XAxis')
    self.DeleteNode('Femur_ZJtAxis')
    self.DeleteNode('Femur_YJtAxis')
    self.DeleteNode('OutSide')
    self.DeleteNode('InSide')
    self.DeleteNode('Tibia_ZAxis')
    self.DeleteNode('Tibia_XAxis')
    self.DeleteNode('Tibia_YAxis')
    self.DeleteNode('Tibia_YZPlane')
    self.DeleteNode('Tibia_XZPlane')
    self.DeleteNode('Tibia_ZJtAxis')
    self.DeleteNode('InSide')

    try:
      self.jiatiload.SetDisplayVisibility(False)
      self.TibiaJiaTiload.SetDisplayVisibility(False)
      self.ChenDian.SetDisplayVisibility(False)
    except Exception as e:
      print(e)
    #获得真实截骨面
  def RealJGM(self,transform1,transform2,name):
    point1, point2, point3 = [0, 0, 0], [0, 0, 0], [0, 0, 0]
    slicer.util.getNode('dc').GetNthControlPointPositionWorld(0, point1)
    slicer.util.getNode('dc').GetNthControlPointPositionWorld(1, point2)
    slicer.util.getNode('dc').GetNthControlPointPositionWorld(2, point3)
    zb = np.array([[point1[0], point1[1], point1[2], 0],
                   [point2[0], point2[1], point2[2], 0],
                   [point3[0], point3[1], point3[2], 0],
                   [0,0,0,1]])
    transformNode = slicer.util.getNode(transform1)
    trans = slicer.util.arrayFromTransformMatrix(transformNode)
    transformNode1 = slicer.util.getNode(transform2)
    trans1 = slicer.util.arrayFromTransformMatrix(transformNode1)
    Trans_ni = np.linalg.inv(trans)
    Trans1_ni = np.linalg.inv(trans1)
    JGM = np.dot(np.dot(Trans_ni,Trans1_ni),zb)
    JieGu = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', name)
    JieGu.AddControlPoint(JGM[0][0], JGM[0][1], JGM[0][2])
    JieGu.AddControlPoint(JGM[1][0], JGM[1][1], JGM[1][2])
    JieGu.AddControlPoint(JGM[2][0], JGM[2][1], JGM[2][2])
    JieGu.SetAndObserveTransformNodeID(transformNode1.GetID())
  
  def PyQtGraph(self):
    self.ui.PopupImage.setVisible(True)
    for i in range (0,len(self.ui.GraphImage.children())):
      a = self.ui.GraphImage.children()[-1]
      a.delete() 

    self.data1 = 0
    self.data2 = 0
    self.ui.GraphImage.setAutoFillBackground(True)
    viewLayout = qt.QVBoxLayout()
    self.ui.GraphImage.setLayout(viewLayout)
    pg.setConfigOption('background', '#454647')
    win = pg.GraphicsLayoutWidget(show=True)
    layout = shiboken2.wrapInstance(hash(viewLayout),QVBoxLayout)
    layout.addWidget(win)
    Y1 = np.array(self.pyqt_data_y1)
    X1 = np.array(self.pyqt_data_x)
    Y2 = np.array(self.pyqt_data_y2)
    X2 = np.array(self.pyqt_data_x)
    pg.setConfigOptions(antialias=True)
    self.p1 = win.addPlot()
    #self.p1.showGrid(True,True,0.1)#网格线
    #画线
    z1 = np.polyfit(X1,Y1,5) #拟合
    z2 = np.polyfit(X2,Y2,5)
    self.pp1 = np.poly1d(z1)#多项式显示
    self.pp2 = np.poly1d(z2)
    xx1 = np.linspace(-10,130,1000)
    yy1 = self.pp1(xx1)
    xx2 = np.linspace(-10,130,1000)
    yy2 = self.pp2(xx1)
    self.fill1=self.p1.plot(xx1,yy1,fillLevel=-0.3, brush=(50,50,200,100))
    self.fill2=self.p1.plot(xx2,yy2,fillLevel=-0.3, brush=(50,50,200,100))
    self.xian1 = self.p1.plot(xx1,yy1,pen="r")
    self.xian2 = self.p1.plot(xx2,yy2,pen="y")
    angle = self.p1.plot([0,0],[0,0],pen='g')

    self.currentX_line = pg.InfiniteLine(angle=90, movable=False, pen='g')
    self.p1.addItem(self.currentX_line, ignoreBounds=True)
    #显示图例
    legend = pg.LegendItem((20,5), offset=(10,5))
    legend.setParentItem(self.p1)
    legend.addItem(self.xian1, '内侧(mm)')
    legend2 = pg.LegendItem((20,5), offset=(10,16))
    legend2.setParentItem(self.p1)
    legend2.addItem(self.xian2, '外侧(mm)')
    legend3 = pg.LegendItem((20,5), offset=(10,27))
    legend3.setParentItem(self.p1)
    legend3.addItem(angle, '角度(°)')
    
    #Y轴
    ay = self.p1.getAxis('left')
    ticks1 = [-20,-10,-3,0,3,10,20]
    ay.setTicks([[(v, str(v)) for v in ticks1 ]])
    #X轴
    ax = self.p1.getAxis('bottom') 
    ticks = [-10,0,10,20,30,40,50,60,70,80,90,100,110,120,130]
    ax.setTicks([[(v, str(v)) for v in ticks ]])  
    #设置线
    #plot画线（x坐标[x1,x2]，y坐标[y1,y2]，线颜色，线宽度，线样式）
    self.l1=self.p1.plot([0,0], [-10,10], pen = '#c8c8c8', linewidth=1,linestyle='-') #90°线
    self.l2=self.p1.plot([90,90], [-10,10], pen = '#c8c8c8', linewidth=1,linestyle='-') #0°线
    l3=self.p1.plot([-10,130], [10,10], pen = '#c8c8c8', linewidth=1,linestyle='-') #10mm线
    l4=self.p1.plot([-10,130], [-10,-10], pen = '#c8c8c8', linewidth=1,linestyle='-') #-10mm线
    #设置文本，anchor用来设置偏移位置
    #显示文本
    text1 = pg.TextItem("%0.1f mm"%(self.pp2(0)))
    self.p1.addItem(text1)
    text1.setPos(0, self.pp2(0)+3)
    text2 = pg.TextItem("%0.1f mm"%(self.pp2(90)))
    self.p1.addItem(text2)
    text2.setPos(90, self.pp2(90)+3)
    self.text3 = pg.TextItem("%0.1f mm"%(self.pp2(0)))
    self.text4 = pg.TextItem("%0.1f mm"%(self.pp2(0)))
    self.p1.addItem(self.text3)
    self.p1.addItem(self.text4)


    # 设置十字线并显示坐标
    label = pg.LabelItem(justify='right',row = 0,column = 1)
    win.addItem(label)
    self.vLine = pg.InfiniteLine(angle=90, movable=False)
    # hLine = pg.InfiniteLine(angle=0, movable=False)
    self.p1.addItem(self.vLine, ignoreBounds=True)
    # p1.addItem(hLine, ignoreBounds=True)

    self.num_of_curves=2
    Colors_Set = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),(44, 160, 44), (152, 223, 138)]
    self.plotcurves = ["%d" % x for x in np.arange(self.num_of_curves)]
    self.curvePoints = ["%d" % x for x in np.arange(self.num_of_curves)]
    self.texts = ["%d" % x for x in np.arange(self.num_of_curves)]
    self.arrows = ["%d" % x for x in np.arange(self.num_of_curves)]
    self.datas = ["%d" % x for x in np.arange(self.num_of_curves)]
 
    for k in range (self.num_of_curves):
      self.plotcurves[k] = pg.PlotCurveItem()

    self.datas[0] = [xx1,yy1]
    self.datas[1] = [xx2,yy2]
    for j in range(self.num_of_curves):
      pen = pg.mkPen(color=Colors_Set[j+2],width=1)
      self.plotcurves[j].setData(x=self.datas[j][0],y=self.datas[j][1],pen=pen,clickable=True)

    for k in range (self.num_of_curves):
      self.p1.addItem(self.plotcurves[k])
      self.curvePoints[k] = pg.CurvePoint(self.plotcurves[k])
      self.p1.addItem(self.curvePoints[k])
      self.texts[k] = pg.TextItem(str(k),color=Colors_Set[k+2],anchor=(0.5,0))
      # Here we require setParent on the TextItem
      self.texts[k].setParentItem(self.curvePoints[k])   
  
    #proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
    self.p1.scene().sigMouseMoved.connect(self.mouseMoved)
    self.p1.hoverEvent = self.hoverEvent
    win.show()
    self.ui.GraphImage.show()

  def hoverEvent(self,event):
    if event.isExit():
      self.vLine.hide()
      for i in range(2):
        self.texts[i].hide()
        # self.arrows[i].hide()
        self.curvePoints[i].hide()
    else:
      self.vLine.show()
      for i in range(2):
        self.texts[i].show()
        # self.arrows[i].show()
        self.curvePoints[i].show()

  def mouseMoved(self,evt):
    pos = self.p1.mapFromScene(evt)
    #pos = evt[0]
    majors = ["内侧","外侧"]
    if self.p1.sceneBoundingRect().contains(pos):
      mousePoint = self.p1.vb.mapSceneToView(pos)
      index = int(mousePoint.x())
      if index >-10 and index < 130:
        self.dataPosX = mousePoint.x()
        for m in range (self.num_of_curves):
          self.curvePoints[m].setPos((float(index)+10)/140)              
          T = majors[m] # Get the respective text string of the Legend
          if m:
            self.texts[m].setText(str(T) + ":[%0.1f,%0.1f]" % (self.dataPosX, self.pp2(self.dataPosX)))
          else:
            self.texts[m].setText(str(T)+":[%0.1f,%0.1f]"%(self.dataPosX,self.pp1(self.dataPosX)))
          self.arrows[m] = pg.ArrowItem(angle=-45)
          self.arrows[m].setParentItem(self.curvePoints[m])

      self.vLine.setPos(mousePoint.x())

  def updatePyqtgraph(self):
    Y1 = np.array(self.pyqt_data_y1)
    X1 = np.array(self.pyqt_data_x)
    Y2 = np.array(self.pyqt_data_y2)
    X2 = np.array(self.pyqt_data_x)
    z1 = np.polyfit(X1, Y1, 5)  # 拟合
    z2 = np.polyfit(X2, Y2, 5)
    self.pp1 = np.poly1d(z1)  # 多项式显示
    self.pp2 = np.poly1d(z2)
    xx1 = np.linspace(-10, 130, 1000)
    yy1 = self.pp1(xx1)
    yy2 = self.pp2(xx1)
    self.datas[0] = [xx1, yy1]
    self.datas[1] = [xx1, yy2]
    self.xian1.setData(xx1, yy1)
    self.xian2.setData(xx1, yy2)
    self.fill1.setData(xx1, yy1)
    self.fill2.setData(xx1, yy2)

    for j in range(2):
      self.plotcurves[j].setData(x=self.datas[j][0], y=self.datas[j][1])
    self.l1.setData([0, 0], [self.pp1(0), self.pp2(0)])
    self.l2.setData([90, 90], [self.pp1(90), self.pp2(90)])

    #添加当前角度
    self.currentX_line.setPos(self.currentX)
    self.text3.setText("%0.1f mm"%(self.pp1(self.currentX)))
    self.text4.setText("%0.1f mm"%(self.pp2(self.currentX)))
    self.text3.setPos(self.currentX, self.pp1(self.currentX)+1.5)
    self.text4.setPos(self.currentX, self.pp2(self.currentX)+1.5)

    if not self.ui.Graph.visible :
      self.ReturnGraph()
    line1 = slicer.util.getNode('InSide').GetLineLengthWorld()
    line2 = slicer.util.getNode('OutSide').GetLineLengthWorld()
    self.JieGuJianXi.SetNthControlPointLabel(0,str(round(line1,2))+'mm')
    self.JieGuJianXi.SetNthControlPointLabel(1,str(round(line2,2))+'mm')
    s1 = 1
    s2 = 1
    s3 = 0  
    s4 = 1
    s5 = round(line1,2)
    s6 = round(line1,2)
    s7 = 0
    s8 = '0@\n'
    self.client.send(f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}'.encode())
    #print('已发送', f'{s1},{s2},{s3},{s4},{s5},{s6},{s7},{s8}')
    time.sleep(0.15)
    

  def PopupGraph(self):
    if self.ui.PopupImage.text == '弹出图像':
      self.ui.Graph.setParent(None)
      self.ui.Graph.setWindowFlags(qt.Qt.WindowStaysOnTopHint)#置于顶层
      y = slicer.app.layoutManager().threeDWidget('View2').height
      x = slicer.app.layoutManager().threeDWidget('View1').width
      xx = slicer.app.layoutManager().threeDWidget('View3').width
      yy = slicer.app.layoutManager().threeDWidget('View3').height
      self.ui.Graph.setGeometry(x+460,y+20,xx,yy)
      self.ui.Graph.show()
      self.ui.PopupImage.setText('恢复图像')
    else:
      self.ReturnGraph()
      self.ui.PopupImage.setText('弹出图像')

  def ReturnGraph(self):
    self.ui.Graph.setParent(self.ui.PopupGraph)
    layout = self.ui.PopupGraph.layout()
    layout.addWidget(self.ui.Graph)
    self.ui.Graph.show()

  def DrawGraph(self):
    pass
  def ClearGraph(self):
    self.p1.clear()    

  def RecordGraph(self):
    pass

  #实时显示内外侧截骨间隙
  def onJieGuJianXi(self):
    self.JieGuJianXi = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', 'JGJX')
    self.JieGuJianXi.AddControlPoint(-50, 10, 0)
    self.JieGuJianXi.AddControlPoint(50, 10, 0)
    self.JieGuJianXi.GetDisplayNode().PointLabelsVisibilityOn()
    self.JieGuJianXi.GetDisplayNode().SetGlyphScale(0)
    self.JieGuJianXi.GetDisplayNode().SetTextScale(3)
    Femur_ZJtAxis = slicer.util.getNode('变换_R')
    self.JieGuJianXi.SetAndObserveTransformNodeID(Femur_ZJtAxis.GetID())
    WaiCeLine = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode','OutSide')
    WaiCeLine.AddControlPoint(0, 0, 0)
    WaiCeLine.AddControlPoint(10, 0, 0)
    WaiCeLine.GetDisplayNode().SetPropertiesLabelVisibility(0)
    WaiCeLine.SetNthControlPointLocked(0,True)
    WaiCeLine.SetNthControlPointLocked(1,True)
    NeiCeLine = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode','InSide')
    NeiCeLine.AddControlPoint(0, 0, 0)
    NeiCeLine.AddControlPoint(10, 0, 0)
    NeiCeLine.GetDisplayNode().SetPropertiesLabelVisibility(0)
    NeiCeLine.SetNthControlPointLocked(0,True)
    NeiCeLine.SetNthControlPointLocked(1,True)

    

  def XuHao(self):
    Number = ["⑳","⑲","⑱","⑰","⑯","⑮","⑭","⑬","⑫","⑪","⑩","⑨","⑧","⑦","⑥","⑤","④","③","②","①"]

  def onstartDJ(self):

    server_ip = "192.168.3.115"
    server_port = 8001
    waitStatu = 1
    while waitStatu:
      try:
        # self.ser = serial.Serial("/dev/rfcomm0", 115200,timeout=0.1) #开启蓝牙串口，波特率为9600
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(None)
        self.client.connect((server_ip, server_port))
        self.client.send("PC".encode())  # 告诉服务端自己的身份
        waitStatu = 0
        print('已连接')
      except:
        print('等待连接')
        waitStatu = 0
        time.sleep(1)
    # received_thread_ = threading.Thread(target=self.recvfunc, args=(self,))
    # # print("thread")
    # self._is_running_ = True
    # # print("thread1")
    # received_thread_.setDaemon(True)
    # # print("thread2")
    # # received_thread_.setName("SerialPortRecvThread")
    # received_thread_.start()
    # print('开始监听信号')


  def recvfunc(self,no=None):
      while 1:
          recv_data = self.client.recv(13686)
          if (recv_data):
              self.buffer = recv_data.decode()
              print('接收到的', self.buffer)
              self.ms.labeltxt.emit(str(self.buffer))
              #self.handleCalc_do(self.buffer)

          else:
              time.sleep(0.01)




  def handleCalc_do(self,s):
      buf_list = s.split('@')
      for i in range(len(buf_list)):
          buf_list1=buf_list[i].split(',')
          print("buf_list1",buf_list1)
          if len(buf_list1)==8:
              self.handleData(buf_list1)

  def handleData(self,buf):
      if int(buf[0]) == 1:
        if int(buf[1]) == 0:
          if int(buf[2])<12:
              print('onSelect1')
              self.onSelect1('xiaopingmu')
          else:
              print('onNextArea')
              self.onNextArea('xiaopingmu')
        else:
          if int(buf[2])<8:
            print('onSelect1')
            self.onSelect1('xiaopingmu')
          else:
            print('onNextArea')
            self.onNextArea('xiaopingmu')

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  def creat_socket(self):
    HOST = '192.168.3.31' # 服务端 IP 地址
    PORT = 8898        # 服务端端口号
    # 创建一个 TCP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.settimeout(None)
    # 绑定 IP 地址和端口号
    server_socket.bind((HOST, PORT))
    # 监听客户端连接请求
    server_socket.listen(1)
    print(f"Server is listening on {HOST}:{PORT}...")
    while True:
      # 等待客户端连接
      client_socket, addr = server_socket.accept()
      while 1:
        try:
          # 接收客户端发送的数据
          data = client_socket.recv(512)
          data = data.decode('utf-8')
          # print(data)
          if data != '':
            self.mysingle.send_data_single.emit(data)
          #   # self.creataaa(data)
          # else:
          #   print("空")
          #   break
          self.VRstate=1
        except:
          break
      # 关闭客户端连接
      client_socket.close()

  def handleData(self,name, trans):
    qt.QApplication.processEvents()
    slicer.app.processEvents()
    try:
        slicer.util.getNode(name).SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans))
    except:
        transnode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', name)
        transnode.SetAndObserveMatrixTransformToParent(slicer.util.vtkMatrixFromArray(trans))
    slicer.modules.transforms.widgetRepresentation().update()

  def VRControl(self,alldata):
    alldata2 = alldata.split('page')
    for data in alldata2:
      if data == '' or data[-1] != 'E':
          continue
      data = 'page'+data
      if data[:4] == 'page':
        data = data[:-1]
        print("=========",data)
        try:
          page = int(data[4])
        except:
          print("11111")
          continue
        if page == 0 and 'trans' in data:
            name = self.findstr('name','trans',data)
            trans_start = data.find('trans') + len('trans')
            trans_str = data[trans_start:].split(',')
            trans = [float(x) for x in trans_str]
            trans = np.array(trans).reshape(4,4) #转换矩阵
            print(trans)
            # self.handleData(name,trans)
            self.mysingle.handleData_single.emit(name,trans)
        elif page == 1:
          if data[5] == 'A':
            print("第一页向下")
            if self.ui.centerWidget.currentIndex == 0:
              if self.ui.stackedWidget_2.currentIndex == 0:
                # self.InitChangePage()
                self.mysingle.InitChangePage_single.emit()
              if self.ui.stackedWidget_2.currentIndex == 1:
                # self.MainChangePage()
                self.mysingle.MainChangePage_single.emit()
        elif page == 2:
          if data[5] == 'A':
            print("第二页向下")
            if self.ui.centerWidget.currentIndex == 2:
              # self.PreparatChangeDownPage(self.ui.stackedWidget)
              if self.ui.stackedWidget.currentIndex == 5:
                # self.MainChangePage()
                self.mysingle.MainChangePage_single.emit()
                # slicer.app.invokeInMainThrea(self.MainChangePage)
              self.mysingle.PreparatChangeDownPage_single.emit()
        elif page == 3:
          if self.ui.centerWidget.currentIndex == 3:
            if data[5] == 'A':
              self.onNextArea()
            else:
              point_start = data.find('point') + len('point')
              point_str = data[point_start:].split(',')
              point = [float(x) for x in point_str]#选点坐标
              print(point)
              self.vrPoint=point
        elif page == 4:
          if self.ui.centerWidget.currentIndex == 4:
            if data[5] == 'A':
              self.onNextArea()
            else:
              point_start = data.find('point') + len('point')
              point_str = data[point_start:].split(',')
              point = [float(x) for x in point_str]#选点坐标
              self.vrPoint=point
        # elif page == 5:
        #   if self.ui.centerWidget.currentIndex == 5:
        #     if data[5] == 'p':
        #       self.ui.stackedWidget_5.setCurrentIndex(int(data[6]))
        #     anglek = float(self.findstr('anglek','valgus',data))
        #     valgus = float(self.findstr('valgus','space0',data))
        #     space0_str = self.findstr('space0','space1',data).split(',')
        #     space0 = [float(x) for x in space0_str]
        #     space1_start = data.find('space1') + len('space1')
        #     space1_str = data[space1_start:].split(',')
        #     space1 = [float(x) for x in space1_str]
        

  def findstr(self,start,end,data):
    start_pos = data.find(start) + len(start)
    end_pos = data.find(end)
    
    return data[start_pos:end_pos]



# # class MySignals(qt.QObject):
# #   # 定义了一个信号，这个信号发给控件的类型是QTextBrowser,发送的消息类型是str字符串
# #   labeltxt = Signal(str)



class Pedal:
    def __init__(self, pushButtons, index):
        shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+Alt+Q"), slicer.util.mainWindow())
        shortcut.connect('activated()', self.SelectPushbutton)

        shortcut1 = qt.QShortcut(qt.QKeySequence("Ctrl+Alt+E"), slicer.util.mainWindow())
        shortcut1.connect('activated()', self.ConfirmSelect)
        #传递进来所有需要点击的按钮
        self.pushButtons = pushButtons
        #传递进来需要切换的按钮组合
        self.index = index
        print("pushButtons",pushButtons)
        print("index",index)
        #当前所有页面的位置
        self.currentStatueIndex=[]
        #上一个页面
        self.PreviousStatue=0
        #当前页面
        self.currentStatue=0
        for i in range(len(self.index)):
          self.currentStatueIndex.append(-1)

    def AllIndexTo0(self):
      for i in range(len(self.index)):
          self.currentStatueIndex[i]=[-1]
      #切换状态后，所有按钮都不突出显示，当前第一个按钮突出显示
      for i in range(len(self.pushButtons)):
          self.pushButtons[i].setStyleSheet("")
      self.pushButtons[self.index[self.currentStatue][0]].setStyleSheet("background-color:red")
      self.currentStatueIndex[self.currentStatue]=0



    def SelectCurrentStatue(self,index):
      #记录当前页为上一个页面
      self.PreviousStatue=self.currentStatue
      self.currentStatue=index
      if self.currentStatue==0:
        self.pushButtons[self.index[self.currentStatue][self.currentStatueIndex[self.currentStatue]]].setStyleSheet("background-color:red")
        return
      self.AllIndexTo0()



    def SelectPushbutton(self):
      #当移动到最后一个时，向第一个移动
      print("self.currentStatueIndex",self.currentStatueIndex)
      print("self.currentStatue",self.currentStatue)
      print("self.index",self.index)
      if self.currentStatueIndex[self.currentStatue]==len(self.index[self.currentStatue])-1:
          self.currentStatueIndex[self.currentStatue]=-1
      self.currentStatueIndex[self.currentStatue]+=1
      for i in range(len(self.index[self.currentStatue])):
          self.pushButtons[self.index[self.currentStatue][i]].setStyleSheet("")
      self.pushButtons[self.index[self.currentStatue][self.currentStatueIndex[self.currentStatue]]].setStyleSheet("background-color:red")

    def ConfirmSelect(self):
      self.pushButtons[self.index[self.currentStatue][self.currentStatueIndex[self.currentStatue]]].click()

# class ReSizeEvent(qt.QObject):
#   def eventFilter(self, object, event):
#     if(event.type() == qt.QEvent.Resize):
#       NoImage = slicer.modules.NoImageWidget
#       if NoImage.currentModel == 3 and NoImage.ui.Adjustment.checked:
#         NoImage.FemurCameraTip()
#       elif NoImage.currentModel == 4 and NoImage.ui.Adjustment2.checked:
#         NoImage.SetTibiaCameraTip()
#       elif NoImage.ui.ForceLine.checked and NoImage.ui.ForceLine2.checked:
#         NoImage.ForceLabel1.setGeometry(NoImage.view1.contentsRect().width()/2-50,5,200,40)
#         NoImage.ForceLabel2.setGeometry(NoImage.view2.contentsRect().width()/2-50,5,200,40)
#       return False
#     return False