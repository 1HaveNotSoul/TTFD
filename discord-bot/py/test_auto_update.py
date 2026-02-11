#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест системы автообновлений
"""

import asyncio
from updates_system import load_auto_update, check_auto_update

def test_load():
    """Тест загрузки автообновления"""
    print("=" * 60)
    print("ТЕСТ ЗАГРУЗКИ АВТООБНОВЛЕНИЯ")
    print("=" * 60)
    
    auto_update = load_auto_update()
    print(f"\nEnabled: {auto_update.get('enabled')}")
    print(f"Changes: {auto_update.get('changes')}")
    
    if auto_update.get('enabled') and auto_update.get('changes'):
        print("\n✅ Автообновление настроено!")
        print("\nИзменения:")
        for i, change in enumerate(auto_update['changes'], 1):
            print(f"  {i}. {change}")
    else:
        print("\n❌ Автообновление не настроено")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_load()
