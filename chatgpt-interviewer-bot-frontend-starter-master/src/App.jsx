import React, { useState } from 'react';
import { Button, Spin } from 'antd';
import { AudioOutlined, StopOutlined } from '@ant-design/icons';
import './App.css';

function App() {
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRecordClick = async () => {
    try {
      // Request access to the user's microphone
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create a MediaRecorder instance
      const mediaRecorder = new MediaRecorder(stream);

      // Set up an array to store audio data chunks
      let audioChunks = [];

      // When data is available, push it to the array
      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      // When recording stops, handle the audio blob
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

        // Automatically send the audio to the backend after stopping
        await sendAudioToBackend(audioBlob);

        // Reset the audioChunks array
        audioChunks = [];
      };

      // Start recording
      mediaRecorder.start();

      // Save the mediaRecorder instance for later use (e.g., stopping the recording)
      window.mediaRecorder = mediaRecorder;

      // Update state to reflect recording status
      setRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  // Helper function to send audio to the backend
  const sendAudioToBackend = async (audioBlob) => {
    setLoading(true); // Show loading spinner while processing
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.wav');

    try {
      const response = await fetch('http://127.0.0.1:8000/talk', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        // Play the audio response from the backend
        const audioStream = await response.blob();
        const audioURL = URL.createObjectURL(audioStream);

        const audio = new Audio(audioURL);
        audio.play();
      } else {
        console.error('Error:', await response.text());
        alert('Failed to process audio. Please try again.');
      }
    } catch (error) {
      console.error('Error sending audio to backend:', error);
      alert('An error occurred. Please check the console for details.');
    } finally {
      setLoading(false); // Hide loading spinner
    }
  };

  const handleStopClick = () => {
    if (window.mediaRecorder) {
      // Stop the MediaRecorder instance
      window.mediaRecorder.stop();

      // Reset the MediaRecorder instance
      window.mediaRecorder = null;

      // Update the state to indicate recording has stopped
      setRecording(false);
    } else {
      console.error('No active recording to stop.');
    }
  };

  const handleClearHistoryClick = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/clear', {
        method: 'GET',
      });

      if (response.ok) {
        const data = await response.json();
        console.log(data.message); // Log success message
        alert('Chat history cleared successfully!');
      } else {
        console.error('Failed to clear history:', response.statusText);
        alert('Failed to clear chat history. Please try again.');
      }
    } catch (error) {
      console.error('Error while clearing chat history:', error);
      alert('An error occurred. Please check the console for details.');
    }
  };

  return (
    <div className="App">
      <div className="button-container">
        <Button
          className={`record-button ${recording ? 'active' : ''}`}
          shape="circle"
          icon={<AudioOutlined />}
          size="large"
          onClick={handleRecordClick}
          disabled={recording || loading} // Disable if already recording or loading
        />
        <Button
          className={`stop-button ${recording ? 'active' : ''}`}
          shape="circle"
          icon={<StopOutlined />}
          size="large"
          onClick={handleStopClick}
          disabled={!recording || loading} // Disable if not recording or loading
        />
        <Button
          className="clear-button"
          shape="rectangle"
          size="large"
          onClick={handleClearHistoryClick}
          disabled={loading} // Disable if loading
        >
          Clear History
        </Button>
      </div>
      {loading && (
        <div className="loading-container">
          <Spin tip="Processing..." />
        </div>
      )}
    </div>
  );
}

export default App;
