

import discord
from discord.ext import commands, tasks
import json
import time
import asyncio
import math
from discord.ui import Button, View, Modal, TextInput
import numpy as np
import traceback
import pprint

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
intents.members = True
client = commands.Bot(command_prefix='!', intents=intents)


class QuizView1(View):
    def __init__(self, num_buttons: int, timeout=5):
        super().__init__(timeout=timeout)
        self.user_presses = {}
        
        self.message = None  # This will store the message reference for later editing

        # Dynamically add buttons
        for i in range(num_buttons):
            button = Button(label=f"Option {i + 1}", custom_id=str(i + 1))
            button.callback = self.capture_response  # Set the callback method for button press
            self.add_item(button)
            
        self.startTime=time.time()
        

    async def on_timeout(self):
        # Disable all buttons when the view times out
        for item in self.children:
            item.disabled = True  # Disable all buttons in the view
        
        # Update the message content to indicate that the quiz has ended
        timeout_message = "Time is up! The quiz has ended."

        # Resend the updated view with disabled buttons
        # if self.message:
            # Edit the message with the updated buttons and new content
        
        await self.message.edit(content=timeout_message, view=self)
        
        # for value in self.user_presses:
        #     value = int(value) - 1
            
        return self.user_presses

    async def capture_response(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        option_selected = interaction.data["custom_id"]  # Get the button ID (option selected)

        # Print selected option for debug purposes
        print(user_id, option_selected)

        # Check if the user has already pressed a button
        if user_id in self.user_presses:
            # await interaction.response.send_message("You have already made a selection!", ephemeral=True)
            await interaction.response.defer()  # Make this response visible only to the user
            return

        # Record the user's selection
        self.user_presses[user_id] = [int(option_selected)-1,time.time()-self.startTime ]
        
        await interaction.response.defer()
        # await interaction.response.send_message(content=f"You selected option {option_selected}.", ephemeral=True)
        
class QuizView(View):
    def __init__(self, num_buttons: int, timeout=5):
        super().__init__(timeout=timeout)
        self.user_presses = {}
        self.message = None  # This will store the message reference for later editing
        self.start_time = time.time()  # Track when the quiz started
        self.remaining_time = timeout  # Countdown duration in seconds

        # Dynamically add buttons
        for i in range(num_buttons):
            button = Button(label=f"Option {i + 1}", custom_id=str(i + 1))
            button.callback = self.capture_response  # Set the callback method for button press
            self.add_item(button)

    async def countdown(self):
        """Update the message every second with remaining time."""
        while self.remaining_time > 0:
            if self.message:
                # Edit the message to show the countdown
                await self.message.edit(content=f"Seconds left: {self.remaining_time}", view=self)
            await asyncio.sleep(1)  # Wait for 1 second
            self.remaining_time -= 1

        # Timeout reached, trigger the timeout event
        await self.on_timeout()

    async def on_timeout(self):
        """Disable buttons and notify that the quiz has ended when the view times out."""
        # Disable all buttons when the view times out
        for item in self.children:
            item.disabled = True  # Disable all buttons in the view
        
        # Update the message content to indicate that the quiz has ended
        timeout_message = "Time is up! The quiz has ended."

        # Resend the updated view with disabled buttons
        if self.message:
            await self.message.edit(content=timeout_message, view=self)
        
        return self.user_presses

    async def capture_response(self, interaction: discord.Interaction):
        """Handle a button press, record the user's selection."""
        user_id = interaction.user.id
        option_selected = interaction.data["custom_id"]  # Get the button ID (option selected)

        # Print selected option for debug purposes
        print(user_id, option_selected)

        # Check if the user has already pressed a button
        if user_id in self.user_presses:
            await interaction.response.defer()  # Make this response visible only to the user
            return

        # Record the user's selection along with the time taken
        # self.user_presses[user_id] = [int(option_selected) - 1, round(time.time() - self.start_time,2)]
         #{time: float, questionType: response: , "isCorrect" }
        self.user_presses[user_id] = {
            "time": round(time.time()-self.start_time,2),
            "response": int(option_selected)-1
        }
        
        await interaction.response.defer()

    async def start_quiz(self, message):
        """Start the quiz and begin the countdown."""
        self.message = message
        await self.countdown()
        
        
class QuizInformation:
    def __init__(self, questionCount:int, members:list, answers: list, moduleId:str, quizId:str, userId:str, questionType: list, memberToUsername) -> None:
        self.memberCount=len(members)
        # self.matrix = np.zeros((self.memberCount, questionCount), dtype=object)
        self.matrix = [[None for _ in range(questionCount)] for _ in range(self.memberCount)]
        self.rows=questionCount
        self.map={}
        self.leaderboard={}
        self.answers=answers
        self.memberToUsername=memberToUsername
        
        self.questionType=questionType
        
        self.moduleId=moduleId
        self.quizId=quizId
        self.timestamp=round(time.time(),2)
        self.userId=userId
        
        self.key = f"{self.moduleId}-{self.quizId}-{self.timestamp}-{self.userId}"

        
        for i in range(self.memberCount):
            self.map[members[i]]=i
            self.leaderboard[members[i]]=0

    def updateIndex(self, discordId, questionIndex, value):
        #{time: float, questionType: response: , "isCorrect" }
         
        # self.matrix[self.map[discordId]][questionIndex]=value
        match self.questionType[questionIndex]:
            case "multiple":
                print(value,discordId,questionIndex)
                if value["response"]==self.answers[questionIndex]:
                    self.leaderboard[discordId]+=1
                    value["isCorrect"]=True
                else:
                    value["isCorrect"]=False
                    
                self.matrix[self.map[discordId]][questionIndex]=value
                pass
            case "multipleAnswer":
                pass
            case "simpleText":
                print(value)
                if value["response"]==self.answers[questionIndex]:
                    self.leaderboard[discordId]+=1
                    value["isCorrect"]=True
                else:
                    value["isCorrect"]=False
                    
                self.matrix[self.map[discordId]][questionIndex]=value
                pass
            case "multipleText":
                return 
            
  
        pprint.pprint(self.matrix)
        

    def sortLeaderboard(self):
        self.leaderboard = dict(sorted(self.leaderboard.items(), key=lambda item: item[1], reverse=True))
        usernameLeaderboard={}
        for key,value in self.leaderboard.items():
            usernameLeaderboard[self.memberToUsername[key]]=value
        
        return usernameLeaderboard
        # return self.leaderboard


    def writeData(self):
        try:
            with open("quizData.json", "r") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return  # If file doesn't exist or is invalid, start with an empty dictionary

        # Append the current quiz data under the unique key
        data[self.key] = {
            "matrix": self.matrix,
            "userToIndex": self.map,
            "questionCount": self.rows,
            "memberCount": self.memberCount,
            "answerArray": self.answers
        }

        # Write the updated data back to the file
        with open("quizData.json", "w") as file:
            json.dump(data, file, indent=4) 



def create_leaderboard_embed(leaderboard):
    embed = discord.Embed(title="Leaderboard", color=0xFFFFFF)

    # Limit to the top 5 entries
    top_entries = list(leaderboard.items())[:5]

    for index, (user_id, score) in enumerate(top_entries, start=1):
        embed.add_field(
            name=f"{index}. User ID: {user_id}", 
            value=f"**Score:** {score}", 
            inline=False
        )

    return embed

        



def formatCode(code, language=None):
    if language==None:
        return code
    
    return f"```{language}\n{code}\n```"




@client.command()
async def quiz(ctx, *, quiz: str):
    
    
    try:
        channel = ctx.channel  # This will get the current channel
        guild = ctx.guild      # The server (guild) where the channel is located
        userId = ctx.author.id
        await guild.chunk()  # This loads all members into cache if not already
        members = []
        memberToUsername={}


        # await ctx.message.delete()
        # print(f"ctx.message: {ctx.message}")
        
        # Loop through all members in the guild
        for member in guild.members:
            if channel.permissions_for(member).read_messages and not member.bot:  # Check if the member can read messages in the channel
                members.append(member.id)  # Append the Discord ID of the member
                memberToUsername[member.id]=member.name
                
        
        print(memberToUsername)
        await ctx.message.delete()
        
        with open("quiz.json","r") as file:
            quizJson=json.load(file)[quiz]
            

        
        questionCount=len(quizJson["questionList"])
        # memberCount=len(members)


        questionType=[]
        answerList=[]
        for i in range(questionCount):
            questionType.append(quizJson["questionList"][i]["choiceType"])
            answerList.append(quizJson["questionList"][i]["answer"])
        print(questionType,answerList)
        # for question in quizJson:
            # question["text"]
        
        # answerList=list(x["answer"] for x in quizJson["questionList"])

            
        quizInformation=QuizInformation(questionCount, members, answerList, "MA102", quiz,str(userId),questionType, memberToUsername)
        

        
        for i in range (len(quizJson["questionList"])):
            currentQuestion=quizJson["questionList"][i]

            questionText=currentQuestion["questionText"]
            imageURL=currentQuestion["imageURL"]
            
            timeLimit=currentQuestion["timeLimit"]
            choiceLanguage=currentQuestion["choiceLanguage"]
            
            embed = discord.Embed(title=f"Q{i+1}) {questionText}")

            
            
            match currentQuestion["choiceType"]:
                case "multiple":
                    
                    optionsText=""
                    optionCount=len(currentQuestion["choiceList"])
                    for j in range(optionCount):
                        
                        optionsText+=f"{j+1}: {formatCode(currentQuestion["choiceList"][j],language=choiceLanguage)}\n"
                    
                    if imageURL is not None:
                        embed.set_image(url=imageURL)

                    await ctx.send(embed=embed)
                    await ctx.send(optionsText)
                    
                    
                

                    view = QuizView(num_buttons=optionCount,timeout=timeLimit)
                    
                    message = await channel.send("Quiz starts now!", view=view)  # Send the initial quiz message
                    await view.start_quiz(message)

                    # Send the message with the view attached
                    
                    # view.message = await ctx.send("Choose an option:", view=view)
                    # await view.wait()
                    user_responses = await view.on_timeout()  # Call on_timeout to finalize
                    print(user_responses)

                    # print(user_responses)
                    print(i)
                    for key, value in user_responses.items():
                        # print(key,value)
                        quizInformation.updateIndex(key, i, value)

                    leaderboard=quizInformation.sortLeaderboard()
                    leaderboardEmbed = create_leaderboard_embed(leaderboard)
                    await ctx.send(embed=leaderboardEmbed)
                    await asyncio.sleep(2)
                    
                    # print(quizInformation)
                    
                    pass 
                case "simpleText":
                    
                    # optionCount=len(currentQuestion["choiceList"])
                    # for j in range(optionCount):
                        
                        # optionsText+=f"{j+1}: {formatCode(currentQuestion["choiceList"][j],language="python")}\n"
                    
                    if imageURL is not None:
                        embed.set_image(url=imageURL)

                    await ctx.send(embed=embed)
                    

                    view = FeedbackView(timeout=5)  # Set a 15-second countdown
                    message = await ctx.send("Click the button to provide feedback!", view=view)
                    await view.start_feedback(message)
                    
                    await view.wait()
                    user_responses = view.data

                    for key, value in user_responses.items():
                        quizInformation.updateIndex(key, i, {"response": value["response"], "time":value["time"]})
                        
                    leaderboard=quizInformation.sortLeaderboard()
                    leaderboardEmbed = create_leaderboard_embed(leaderboard)
                    await ctx.send(embed=leaderboardEmbed)
                    await asyncio.sleep(2)

                    
                    
                    pass
            
            # await asyncio.sleep(4)
        quizInformation.writeData()   
            

    except Exception as e:
        print('ok')
        
        
class MyView(View):
    def __init__(self):
        super().__init__()

    async def button_callback(self, interaction: discord.Interaction):
        # Access button label from the interaction's custom_id
        button_label = interaction.data["custom_id"]
        await interaction.response.send_message(f"You clicked {button_label}!", ephemeral=True)


 
    
class FeedbackModal(Modal):
    def __init__(self, feedback_view):
        super().__init__(title="Feedback Form")
        self.feedback_view = feedback_view  # Reference to the FeedbackView instance

        # Add a TextInput for user feedback
        self.feedback = TextInput(
            label="Provide feedback",
            style=discord.TextStyle.long,
            placeholder="Enter your feedback here...",
            required=True,
            max_length=500
        )
        self.add_item(self.feedback)

    async def on_submit(self, interaction: discord.Interaction):
        # Check if the feedback view has timed out
        if self.feedback_view.remaining_time <= 0:
            await interaction.response.send_message("Feedback submission is closed.", ephemeral=True)
            return

        # Store the feedback submission and the timestamp
        feedback_data = {
            # 'user_id': interaction.user.id,
            'response': self.feedback.value,
            'time': round(time.time(), 2)
        }

        # Send a response to the user
        await interaction.response.send_message(f"Thanks for your feedback!", ephemeral=True)

        # Store the feedback data in the FeedbackView's data dict
        self.feedback_view.data[interaction.user.id] = feedback_data

        # You could also print the feedback data here
        print(feedback_data)



class SubmitButton(Button):
    def __init__(self, feedback_view):
        super().__init__(label="Submit Feedback", style=discord.ButtonStyle.primary)
        self.feedback_view = feedback_view  # Reference to the FeedbackView instance
        self.user_presses = {}  # Store which users have already submitted

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        # Check if user has already submitted
        if user_id in self.user_presses:
            await interaction.response.send_message("You have already submitted!", ephemeral=True)
            return

        # If they haven't submitted yet, open the modal and mark them as submitted
        self.user_presses[user_id] = time.time()
        value = await interaction.response.send_modal(FeedbackModal(self.feedback_view))  # Pass the feedback view


class FeedbackView(View):
    def __init__(self, timeout=15):
        super().__init__(timeout=timeout)
        self.submit_button = SubmitButton(self)  # Pass self to the button
        self.add_item(self.submit_button)
        self.message = None
        self.remaining_time = timeout  # Track remaining time
        self.data = {}

    async def countdown(self):
        """Update the message every second with remaining time."""
        while self.remaining_time > 0:
            if self.message:
                # Edit the message to show the countdown and update the view
                await self.message.edit(content=f"Click the button to provide feedback! Time left: {self.remaining_time}s", view=self)
            await asyncio.sleep(1)  # Wait for 1 second
            self.remaining_time -= 1

        # Once time is up, trigger timeout
        await self.on_timeout()

    async def on_timeout(self):
        """Disable the button and notify that the submission period has ended."""
        # Disable all buttons when the view times out
        for item in self.children:
            item.disabled = True
        
        # Update the message to indicate the time is up
        if self.message:
            await self.message.edit(content="Time is up! Feedback submission is closed.", view=self)

    async def start_feedback(self, message):
        """Start the feedback submission process and begin countdown."""
        self.message = message
        await self.countdown()  # Start the countdown loop
    
    
    
# Create a command to trigger the feedback button
@client.command()
async def start_feedback(ctx):
    view = FeedbackView(timeout=5)  # Set a 15-second countdown
    message = await ctx.send("Click the button to provide feedback!", view=view)
    await view.start_feedback(message)
    
    await view.wait()
    feedback_data = view.data
    print(feedback_data)
    

    
