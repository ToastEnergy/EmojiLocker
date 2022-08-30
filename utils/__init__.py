import discord

async def bulk_lock(interaction: discord.Interaction, emojis: list[discord.Emoji], roles: list[discord.Role], ignore_persistent: bool = False):
    succesful = 0
    failed = 0
    try:
        await interaction.edit_original_response(content='Working...', view=None, embed=None)
        i = 0
        for emoji in emojis:
            try:
                await emoji.edit(name=emoji.name, roles=roles)
                succesful += 1
            except:
                failed += 1
            i += 1
            await interaction.edit_original_response(content=f'{i}/{len(emojis)}')
        await interaction.edit_original_response(content=None, embed=discord.Embed(title=f'{succesful} succesful, {failed} failed'), view=UpvoteView())
    except Exception as e:
        raise e
    finally:
        interaction.view.stop()