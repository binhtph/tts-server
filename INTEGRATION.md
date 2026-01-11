
## 4. Advanced: Manual Configuration (Node-RED Style) - Direct File Save

 This method saves the audio file directly to the OwnTone `tts` folder so OwnTone plays it as a **local file**.

### Architecture Diagram

```mermaid
sequenceDiagram
    participant HASS as Home Assistant
    participant TTS as TTS API (172.16.100.252:8001)
    participant FS as Shared Folder (/srv/media)
    participant OT as OwnTone (172.16.100.252:3689)
    participant SPK as Speakers

    Note over HASS, OT: 1. Generation Phase
    HASS->>TTS: POST /tts (Text + Model)
    TTS-->>HASS: Returns Audio Stream (WAV)
    HASS->>FS: Saves stream to "owntone.wav" via curl
    
    Note over HASS, OT: 2. Playback Phase
    HASS->>OT: API: Clear Queue
    HASS->>OT: API: Add Item "file:///srv/media/owntone.wav"
    HASS->>OT: API: Play
    OT->>FS: Reads "owntone.wav"
    OT->>SPK: Plays Audio
```

### Prerequisites (Critical)
1.  **Shared Volume**: Your Home Assistant container **MUST** have access to the `tts-server/owntone/tts` folder.
    -   You need to map the folder (e.g., `- /path/to/tts-server/owntone/tts:/media/tts`) in your Home Assistant `docker-compose.yml`.
    -   Verify that HASS can write to this folder.

### A. Define the Shell Command (Download to Shared Folder)

Update your `configuration.yaml`. This command downloads the WAV from the API (at `172.16.100.252`) and saves it directly to the folder OwnTone watches.

*Change `/media/tts/` to the path where you mounted the folder inside Home Assistant.*

```yaml
shell_command:
  tts_download_to_server: >-
    curl -X POST 
    -H "Content-Type: application/json" 
    -d '{"text": "{{ text }}", "model_name": "{{ model_name }}", "speed": {{ speed | int }}}' 
    "http://172.16.100.252:8001/tts" 
    --output "/media/tts/owntone.wav"
```

### B. Define REST Commands for OwnTone

```yaml
rest_command:
  owntone_clear:
    url: "http://172.16.100.252:3689/api/queue/clear"
    method: PUT
  
  owntone_add_item:
    # Use 'file://' URI to play the local file inside the OwnTone container
    url: "http://172.16.100.252:3689/api/queue/items/add?uri=file:///srv/media/owntone.wav"
    method: POST
    
  owntone_play:
    url: "http://172.16.100.252:3689/api/player/play"
    method: PUT
```

### C. Create the Script

```yaml
script:
  tts_direct_save:
    alias: "TTS: Direct Save & Play"
    fields:
      text:
        description: "Text to speak"
        example: "Xin chào"
      model_name:
        description: "Model name"
        default: "ngocngan3701"
      speed:
        description: "Speed"
        default: 1.0
    sequence:
      # 1. Download WAV directly to the shared media folder
      - service: shell_command.tts_download_to_server
        data:
          text: "{{ text }}"
          model_name: "{{ model_name }}"
          speed: "{{ speed }}"
      
      # 2. Wait for file write to complete
      - delay: "00:00:01"

      # 3. Queue and Play
      - service: rest_command.owntone_clear
      - service: rest_command.owntone_add_item
      - service: rest_command.owntone_play
```

### D. Troubleshooting

-   **Debug Command**: If you are unsure what the API is returning or getting 422 errors, run this command on your terminal to test:
    ```bash
    curl -v -X POST -H "Content-Type: application/json" -d '{"text": "xin chao", "model_name": "ngocngan3701", "speed": 1}' http://172.16.100.252:8001/tts --output test.wav
    ```
    (Check the content of `test.wav`. If it plays, the API handles binary response correctly. If it's text, you need to adjust processing.)
