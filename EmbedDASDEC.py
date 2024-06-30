import requests
import json
import sys
import argparse
import time
import serial
from discord_webhook import DiscordEmbed, DiscordWebhook

# Load configuration data
with open("ConfigDAS.json", "r") as f:
    configData = json.load(f)

port = configData['SerialPort']
StationTitle = configData['StationTitle']
StationURL = configData['StationURL']
Description = configData['Description']
webhooks = configData['webhooks']
embed_color = configData.get('EmbedColor', '0x800080')

def main(content):
    description = 'Data received'

    if len(content) == 3:
        embed = create_embed(content[0], description, content[1], content[2])
    elif len(content) == 4:
        if 'Received ' in content[0]:
            embed = create_embed(content[1], content[0], content[2], content[3])
        else:
            embed = create_embed(content[0], description, content[1], content[3], extra_text=content[2])
    elif len(content) == 5:
        embed = create_embed(content[1], content[0], content[2], content[4], extra_text=content[3])
    else:
        print("Error: Unexpected content length.")
        return

    for webhook_url in webhooks:
        webhook = DiscordWebhook(url=webhook_url)
        webhook.add_embed(embed)
        response = webhook.execute()
        if response.status_code == 200:
            print("Successfully posted to webhook\n")
        else:
            print(f"Failed to post to webhook. Status code: {response.status_code}")

def create_embed(title, description, eas_text_data, eas_protocol_data, extra_text=None):
    embed = DiscordEmbed(title=title, description=description, color=embed_color)
    embed.set_author(name=StationTitle, url=StationURL)
    embed.set_footer(text=Description)
    embed.set_timestamp()
    embed.add_embed_field(name='EAS Text Data:', value=eas_text_data, inline=False)
    if extra_text:
        embed.add_embed_field(name='Extra Text:', value=extra_text, inline=False)
    embed.add_embed_field(name='Raw ZCZC Data:', value=f'```{eas_protocol_data}```\nClick to copy', inline=False)
    return embed

def formatting(data4):
    data = []
    data2 = []
    data3 = filter(None, data4.replace('\r', '').split('\n'))
    for i in data3:
        data.append(i)
    for item in data:
        if 'Received at' in item:
            data2.append(item)
            data.remove(item)
            data.insert(0, '')
        elif 'Alert Forwarded' in item:
            data2.append(item)
            data.remove(item)
            data.insert(0, '')
        elif 'Local Alert' in item:
            data2.append(item)
            data.remove(item)
            data.insert(0, '')
    data = ''.join(data).split('ZCZC-')
    data2.append(data[0])
    data2.append('ZCZC-' + data[1])
    return data2

def AHHH(data):
    content = []
    try:
        if len(data) >= 3:
            content.append(data[0])
            issued_split = data[1].lower().split(' issued ')
            if len(issued_split) > 1:
                alert_type_split = issued_split[1].split(' for ')
                if len(alert_type_split) > 1:
                    content.append(alert_type_split[0].strip().upper())
                else:
                    content.append("Unknown Alert Type")
            else:
                content.append("Unknown Alert Type")

            if '.  ' in data[1]:
                split_data = data[1].split('.  ')
                if len(split_data) > 1:
                    content.append(split_data[0].strip() + '.')
                    content.append(''.join(split_data[1:]).strip())
                else:
                    content.append(data[1].strip())
            else:
                content.append(data[1].strip())

            content.append(data[2].strip())
        else:
            issued_split = data[0].lower().split(' issued ')
            if len(issued_split) > 1:
                alert_type_split = issued_split[1].split(' for ')
                if len(alert_type_split) > 1:
                    content.append(alert_type_split[0].strip().upper())
                else:
                    content.append("Unknown Alert Type")
            else:
                content.append("Unknown Alert Type")

            if '.  ' in data[0]:
                split_data = data[0].split('.  ')
                if len(split_data) > 1:
                    content.append(split_data[0].strip() + '.')
                    content.append(''.join(split_data[1:]).strip())
                else:
                    content.append(data[0].strip())
            else:
                content.append(data[0].strip())

            if len(data) > 1:
                content.append(data[1].strip())
    except IndexError as e:
        print(f"Error processing data: {data}. Error: {e}")
        raise e 
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise e 

    return content

list = []
ser = serial.Serial(port=port, baudrate=9600, bytesize=8, stopbits=1)
if ser.isOpen():
    print("Awaiting... data.")
    while True:
        list.append(str(ser.read().decode('utf-8')))
        if '<ENDECSTART>' in ''.join(list):
            list = []
            print("DATA START")
            test = True
            while test:
                list.append(str(ser.read().decode('utf-8')))
                if '<ENDECEND>' in ''.join(list):
                    test = False
                    print('DATA END\n')
                    print("Data:")
                    content = ''.join(''.join(list).split("<ENDECEND>"))
                    print(content)
                    try:
                        main(AHHH(formatting(content)))
                    except Exception as e:
                        print(f"Error: {e}")
                    list = []
                    break
else:
    print("That wasn't supposed to happen...")
    print("The serial port could not be opened.")
