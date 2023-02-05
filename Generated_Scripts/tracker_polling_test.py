import openvr
import time

# initialize OpenVR
vr = openvr.init(openvr.VRApplication_Scene)

# get the head tracking quaternion at 250 Hz
while True:
    poses = vr.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0, openvr.k_unMaxTrackedDeviceCount)
    head_pose = poses[openvr.k_unTrackedDeviceIndex_Hmd]
    head_quat = head_pose.mDeviceToAbsoluteTracking.rotation
    print("Head Quaternion:", head_quat)
    time.sleep(1/250)

# cleanup OpenVR
openvr.shutdown()