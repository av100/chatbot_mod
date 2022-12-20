

import re
async def send_message(message, user_message):
    try:
        ab=None
        if isinstance(message,discord.Interaction):
            await message.response.defer(ephemeral=isPrivate)
            sss = await responses.handle_response(user_message)
            response = f'>{user_message}\n'+re.sub(r"\A[\n\s]*",'',sss,re.MULTILINE)
            ab=message.followup
        elif isinstance(message,discord.Message):
            sss = await responses.handle_response(user_message)
            response = re.sub(r"\A[\n\s]*", '', sss, re.MULTILINE)
            ab=message.channel
        else:
            raise Exception(f"Странное сообщение, {message}")
        if len(response)>1900:
            if "```" in response:
                parts = response.split("```")
                await ab.send(parts[0])
                code_block = parts[1].split("\n")
                formatted_code_block = ""
                for line in code_block:
                    while len(line)>50:
                        formatted_code_block += line[:50]+"\n"
                        line = line[50:]
                    formatted_code_block += line+"\n"
                await ab.send("```"+formatted_code_block+"```")
                await ab.send(parts[2])
            else:
                response_chunks = [response[i:i+1900]
                                   for i in range(0, len(response), 1900)]
                for chunk in response_chunks:
                    await ab.send(chunk)
        else:
            if isinstance(ab,discord.TextChannel):
                await ab.send(response,reference=message)
            else:
                await ab.send(response)
    except Exception as e:
        if ab:
            await ab.send(f"> **Error: Something [{e}] went wrong, please try again later!**")
            
            
            
            