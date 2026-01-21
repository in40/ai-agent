#!/usr/bin/env python3
"""
Script to edit system LLM prompts for all requests.
This script allows users to view, edit, create, and manage system prompts
that are stored separately from the code.
"""

import os
import sys
from pathlib import Path
from utils.prompt_manager import PromptManager


def display_menu():
    """Display the main menu options."""
    print("\n" + "="*50)
    print("LLM Prompt Management System")
    print("="*50)
    print("1. List all available prompts")
    print("2. View a specific prompt")
    print("3. Edit an existing prompt")
    print("4. Create a new prompt")
    print("5. Delete a prompt")
    print("6. Exit")
    print("="*50)


def list_prompts(pm):
    """List all available prompts."""
    prompts = pm.list_prompts()
    if prompts:
        print("\nAvailable prompts:")
        for i, prompt_name in enumerate(prompts, 1):
            print(f"  {i}. {prompt_name}")
    else:
        print("\nNo prompts found.")


def view_prompt(pm):
    """View the content of a specific prompt."""
    prompt_name = input("\nEnter the name of the prompt to view: ").strip()
    content = pm.get_prompt(prompt_name)
    
    if content:
        print(f"\nContent of '{prompt_name}':")
        print("-" * 40)
        print(content)
        print("-" * 40)
    else:
        print(f"\nPrompt '{prompt_name}' not found.")


def edit_prompt(pm):
    """Edit an existing prompt."""
    prompt_name = input("\nEnter the name of the prompt to edit: ").strip()
    current_content = pm.get_prompt(prompt_name)
    
    if not current_content:
        print(f"\nPrompt '{prompt_name}' not found.")
        return
    
    print(f"\nCurrent content of '{prompt_name}':")
    print("-" * 40)
    print(current_content)
    print("-" * 40)
    
    print("\nEnter the new content for the prompt (press Enter on an empty line to finish):")
    new_lines = []
    while True:
        line = input()
        if line == "":
            break
        new_lines.append(line)
    
    new_content = "\n".join(new_lines)
    
    if new_content.strip() != current_content.strip():
        confirm = input(f"\nDo you want to update '{prompt_name}'? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            if pm.update_prompt(prompt_name, new_content):
                print(f"\nPrompt '{prompt_name}' updated successfully.")
            else:
                print(f"\nFailed to update prompt '{prompt_name}'.")
        else:
            print("\nUpdate cancelled.")
    else:
        print("\nNo changes were made.")


def create_prompt(pm):
    """Create a new prompt."""
    prompt_name = input("\nEnter the name for the new prompt: ").strip()
    
    if pm.get_prompt(prompt_name):
        print(f"\nPrompt '{prompt_name}' already exists.")
        return
    
    print("\nEnter the content for the new prompt (press Enter on an empty line to finish):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    content = "\n".join(lines)
    
    if content.strip():
        confirm = input(f"\nDo you want to create '{prompt_name}' with the above content? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            if pm.create_prompt(prompt_name, content):
                print(f"\nPrompt '{prompt_name}' created successfully.")
            else:
                print(f"\nFailed to create prompt '{prompt_name}'.")
        else:
            print("\nCreation cancelled.")
    else:
        print("\nNo content provided. Prompt not created.")


def delete_prompt(pm):
    """Delete an existing prompt."""
    prompt_name = input("\nEnter the name of the prompt to delete: ").strip()
    content = pm.get_prompt(prompt_name)
    
    if not content:
        print(f"\nPrompt '{prompt_name}' not found.")
        return
    
    print(f"\nContent of '{prompt_name}':")
    print("-" * 40)
    print(content)
    print("-" * 40)
    
    confirm = input(f"\nAre you sure you want to delete '{prompt_name}'? This action cannot be undone. (y/N): ").strip().lower()
    if confirm in ['y', 'yes']:
        if pm.delete_prompt(prompt_name):
            print(f"\nPrompt '{prompt_name}' deleted successfully.")
        else:
            print(f"\nFailed to delete prompt '{prompt_name}'.")
    else:
        print("\nDeletion cancelled.")


def main():
    """Main function to run the prompt management system."""
    # Initialize the prompt manager
    pm = PromptManager("./core/prompts")
    
    print("Welcome to the LLM Prompt Management System!")
    
    while True:
        display_menu()
        choice = input("\nSelect an option (1-6): ").strip()
        
        if choice == '1':
            list_prompts(pm)
        elif choice == '2':
            view_prompt(pm)
        elif choice == '3':
            edit_prompt(pm)
        elif choice == '4':
            create_prompt(pm)
        elif choice == '5':
            delete_prompt(pm)
        elif choice == '6':
            print("\nExiting the Prompt Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please select a number between 1 and 6.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()