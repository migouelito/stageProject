import asyncio
import websockets
import json
from datetime import datetime

async def send_positions():
    # Connexion au WebSocket avec user_id dans l'URL
    uri = "wss://winds-wages-switch-oh.trycloudflare.com/ws/positions/"
    reconnect_delay = 5  # Délai de reconnexion en secondes
    
    while True:  # Boucle de reconnexion principale
        try:
            print(f"Tentative de connexion à {uri}")
            async with websockets.connect(
                uri,
                ping_interval=20,
                ping_timeout=60
            ) as websocket:
                print("Connexion WebSocket établie avec succès")
                
                while True:  # Boucle d'envoi des positions
                    try:
                        # Données de position fixes avec type d'animal
                        position_data = {
                            "positions": [{
                                "tracker_id": 1001,
                                "latitude": 12.39558,
                                "longitude": -1.533435,
                                "timestamp": datetime.now().isoformat(),
                                "type_animal": "boeuf"  # Type de l’animal
                            }]
                        }
                        
                        # Envoi des données de position
                        await websocket.send(json.dumps(position_data))
                        print(f"Position envoyée: {position_data['positions'][0]}")
                        
                        # Pause avant le prochain envoi
                        await asyncio.sleep(1)
                        
                    except websockets.exceptions.ConnectionClosed as e:
                        print(f"Erreur pendant l'envoi: {e.code} - {e.reason}")
                        break
                    except Exception as e:
                        print(f"Erreur inattendue: {str(e)}")
                        await asyncio.sleep(1)
                        
        except websockets.exceptions.InvalidURI:
            print("URL WebSocket invalide")
            return
        except Exception as e:
            print(f"Échec de connexion: {str(e)}")
        
        print(f"Tentative de reconnexion dans {reconnect_delay}s...")
        await asyncio.sleep(reconnect_delay)

if __name__ == "__main__":
    try:
        asyncio.run(send_positions())
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")

