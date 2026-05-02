import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import (
    Input, Conv2D, MaxPooling2D, BatchNormalization, 
    GlobalAveragePooling2D, LSTM, Dense, Dropout, 
    TimeDistributed, Flatten
)

def create_gesture_model(frames_n=16, img_size=128, channels=3, num_classes=10):
    """
    Creates the Research-Level CNN + LSTM Gesture Recognition Model.
    
    Architecture:
    1. TimeDistributed CNN (Frame-level features)
    2. LSTM (Temporal modeling)
    3. Classification Head
    """
    
    # --- 1. Processing Input ---
    # Shape: (Batch, Frames, Height, Width, Channels)
    input_shape = (frames_n, img_size, img_size, channels)
    video_input = Input(shape=input_shape, name="video_input")
    
    # --- 2. CNN Feature Extractor (Shared Weights) ---
    # This runs on each frame independently via TimeDistributed
    cnn = Sequential(name="cnn_feature_extractor")
    
    # Block 1
    cnn.add(Conv2D(32, (3, 3), padding='same', activation='relu', input_shape=(img_size, img_size, channels)))
    cnn.add(BatchNormalization())
    cnn.add(MaxPooling2D(pool_size=(2, 2)))
    
    # Block 2
    cnn.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
    cnn.add(BatchNormalization())
    cnn.add(MaxPooling2D(pool_size=(2, 2)))
    
    # Block 3
    cnn.add(Conv2D(128, (3, 3), padding='same', activation='relu'))
    cnn.add(BatchNormalization())
    cnn.add(MaxPooling2D(pool_size=(2, 2)))
    
    # Block 4
    cnn.add(Conv2D(256, (3, 3), padding='same', activation='relu'))
    cnn.add(BatchNormalization())
    # Global Average Pooling reduces (16, 16, 256) -> (256,)
    cnn.add(GlobalAveragePooling2D())
    
    # --- 3. TimeDistributed Wrapper ---
    # Output shape: (Batch, Frames, 256)
    x = TimeDistributed(cnn)(video_input)
    
    # --- 4. LSTM Temporal Modeling ---
    # LSTM Layer 1
    x = LSTM(128, return_sequences=True)(x)
    x = Dropout(0.3)(x)
    
    # LSTM Layer 2 - Last hidden state only (return_sequences=False)
    x = LSTM(64, return_sequences=False)(x)
    x = Dropout(0.3)(x)
    
    # --- 5. Classification Head ---
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.3)(x)
    
    output = Dense(num_classes, activation='softmax', name="gesture_output")(x)
    
    # --- 6. Compile Model ---
    model = Model(inputs=[video_input], outputs=[output])
    
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

if __name__ == "__main__":
    # Quick sanity check
    model = create_gesture_model(frames_n=16, num_classes=10)
    model.summary()
    print("\nModel created successfully.")
