def create_gesture_event(gesture_name, timestamp):
    #Creates a standardized gesture event that can be used by others parts of SlideKick
    gesture_event = {
        "event_type" : "gesture",
        "gesture" : gesture_name,
        "timestamp" : timestamp
    }
    
    return gesture_event

def create_landmark_event(hand_landmarks, timestamp):
    #Stores all detected hand landmarks in a standardized format
    landmarks = []
    
    for index, landmark in enumerate(hand_landmarks):
        
        #Stores the landmark number and its normalized coordinates
        #Landmark detection could produce
        #         {
        #     "event_type": "landmarks",
        #     "timestamp": 48295.382,
        #     "landmarks": [
        #         {
        #             "id": 0,
        #             "x": 0.514,
        #             "y": 0.782,
        #             "z": -0.003
        #         },
        #         {
        #             "id": 1,
        #             "x": 0.487,
        #             "y": 0.701,
        #             "z": -0.021
        #         }
        #         # ...through landmark 20
        #     ]
        # }
        landmark_data = {
            "id": index,
            "x": landmark.x,
            "y": landmark.y,
            "z": landmark.z
        }
        
        landmarks.append(landmark_data)
        
    #Creates a standardized landmark event that can be used by other parts of SlideKick
    #A right swipe could eventually produce 
    # {
    # "event_type": "gesture",
    # "gesture": "swipe_right",
    # "timestamp": 48295.382
    # }
    landmark_event = {
        "event_type": "landmarks",
        "timestamp": timestamp,
        "landmarks": landmark
    }
    
    return landmark_event