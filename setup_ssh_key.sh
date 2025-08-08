#!/bin/bash

# Script pour configurer une clé SSH avec la VM Azure

VM_IP="52.224.120.195"
VM_USER="azureuser"

echo "🔑 Configuration de la clé SSH pour la VM Azure"
echo "==============================================="
echo ""

# Vérifier si une clé existe déjà
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "📝 Génération d'une nouvelle clé SSH..."
    ssh-keygen -t rsa -b 4096 -C "azure-vm-key" -f ~/.ssh/id_rsa -N ""
    echo "✅ Clé SSH générée"
else
    echo "✅ Clé SSH existante trouvée"
fi

echo ""
echo "📤 Copie de la clé publique vers la VM..."
echo "Vous allez devoir entrer votre mot de passe:"
ssh-copy-id $VM_USER@$VM_IP

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Clé SSH configurée avec succès!"
    echo "Vous pouvez maintenant vous connecter sans mot de passe:"
    echo "  ssh $VM_USER@$VM_IP"
    echo ""
    echo "Et déployer avec:"
    echo "  ./deploy_azure.sh"
else
    echo "❌ Erreur lors de la configuration de la clé SSH"
fi