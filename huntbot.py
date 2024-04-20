from ultralytics import YOLO

path = ""
############ NEW MODEL ############
# model = YOLO('yolov8s.pt')

# results = model.train(
#     data=path,
#     device="cpu",
#     cos_lr=True,
#     warmup_epochs=15,
#     box=8,
#     label_smoothing=0.2,
#     dropout=0.5,
#     weight_decay=0.001,
#     epochs=50,
#     imgsz=640)

# ############ RESUME TRAINING ############
# model = YOLO(path + r"\last")

# results = model.train(resume=True)

############ PREDICT ############
model = YOLO(path + r"\best")

results = model.predict(r"C:\Users\ducna\Desktop\huntbot\captchas",
                        visualize=True,
                        augment=True,
                        conf=0.15,
                        max_det=5,
                        save=True,
                        show_conf=False,
                        show_boxes=True,
                        save_txt=True
                        )
