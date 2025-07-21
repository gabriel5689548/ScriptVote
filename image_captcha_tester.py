#!/usr/bin/env python3
"""
Image CAPTCHA Testing Script
Script pour tester la résolution d'images CAPTCHA via 2Captcha
"""

import os
import time
import logging
import argparse
import requests
import base64
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageCaptchaTester:
    def __init__(self, api_key: str, timeout: int = 300):
        self.api_key = api_key
        self.timeout = timeout
        self.driver = None
        
    def setup_driver(self, headless: bool = False):
        """Configure le driver Selenium"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

    def get_captcha_image(self, url: str) -> Optional[str]:
        """Récupère l'image CAPTCHA et la convertit en base64"""
        logger.info(f"Récupération de l'image CAPTCHA depuis: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Recherche de l'image CAPTCHA
            image_selectors = [
                "img[src*='captcha']",
                "img[alt*='captcha']",
                ".captcha img",
                "#captcha-image",
                "img[id*='captcha']"
            ]
            
            for selector in image_selectors:
                try:
                    img_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Obtenir l'image en base64
                    img_base64 = self.driver.execute_script("""
                        var canvas = document.createElement('canvas');
                        var ctx = canvas.getContext('2d');
                        var img = arguments[0];
                        canvas.width = img.width;
                        canvas.height = img.height;
                        ctx.drawImage(img, 0, 0);
                        return canvas.toDataURL('image/png').split(',')[1];
                    """, img_element)
                    
                    if img_base64:
                        logger.info("Image CAPTCHA récupérée avec succès")
                        return img_base64
                        
                except NoSuchElementException:
                    continue
                    
            logger.error("Aucune image CAPTCHA trouvée")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération: {str(e)}")
            return None

    def solve_image_captcha(self, image_base64: str) -> Optional[str]:
        """Résout l'image CAPTCHA via 2Captcha"""
        logger.info("Envoi de l'image à 2Captcha...")
        
        # Soumission
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            'key': self.api_key,
            'method': 'base64',
            'body': image_base64,
            'json': 1
        }
        
        try:
            response = requests.post(submit_url, data=submit_data, timeout=30)
            result = response.json()
            
            if result['status'] != 1:
                logger.error(f"Erreur soumission: {result}")
                return None
                
            captcha_id = result['request']
            logger.info(f"Image soumise avec ID: {captcha_id}")
            
        except Exception as e:
            logger.error(f"Erreur soumission: {str(e)}")
            return None

        # Récupération
        get_url = "http://2captcha.com/res.php"
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                time.sleep(5)
                
                response = requests.get(get_url, params={
                    'key': self.api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }, timeout=30)
                
                result = response.json()
                
                if result['status'] == 1:
                    logger.info(f"CAPTCHA résolu: {result['request']}")
                    return result['request']
                elif result['request'] == 'CAPCHA_NOT_READY':
                    logger.info("Résolution en cours...")
                    continue
                else:
                    logger.error(f"Erreur résolution: {result}")
                    return None
                    
            except Exception as e:
                logger.error(f"Erreur récupération: {str(e)}")
                continue
                
        logger.error("Timeout résolution")
        return None

    def inject_solution(self, solution: str) -> bool:
        """Injecte la solution dans le champ texte"""
        logger.info(f"Injection de la solution: {solution}")
        
        try:
            input_selectors = [
                "input[name*='captcha']",
                "input[id*='captcha']",
                ".captcha-input",
                "#captcha-code",
                "input[placeholder*='captcha' i]"
            ]
            
            for selector in input_selectors:
                try:
                    input_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    input_element.clear()
                    input_element.send_keys(solution)
                    logger.info(f"Solution injectée dans: {selector}")
                    return True
                except NoSuchElementException:
                    continue
                    
            logger.error("Champ de saisie CAPTCHA non trouvé")
            return False
            
        except Exception as e:
            logger.error(f"Erreur injection: {str(e)}")
            return False

    def run_test(self, url: str, headless: bool = False) -> bool:
        """Exécute le test complet"""
        try:
            self.setup_driver(headless)
            
            # Récupérer l'image
            image_base64 = self.get_captcha_image(url)
            if not image_base64:
                return False
                
            # Résoudre le CAPTCHA
            solution = self.solve_image_captcha(image_base64)
            if not solution:
                return False
                
            # Injecter la solution
            if not self.inject_solution(solution):
                return False
                
            logger.info("✅ Test d'image CAPTCHA terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur générale: {str(e)}")
            return False
            
        finally:
            if self.driver:
                self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Testeur d\'image CAPTCHA')
    parser.add_argument('--url', required=True, help='URL contenant l\'image CAPTCHA')
    parser.add_argument('--headless', action='store_true', help='Mode headless')
    
    args = parser.parse_args()
    
    load_dotenv()
    api_key = os.getenv('TWOCAPTCHA_API_KEY')
    
    if not api_key:
        logger.error("Clé API manquante")
        return
        
    tester = ImageCaptchaTester(api_key)
    tester.run_test(args.url, args.headless)

if __name__ == "__main__":
    main()