import { Injectable } from "@angular/core";

@Injectable({ providedIn: 'root' })
export class DiagramBuilderService {


    addNewNode(nodetype: string, newKey: any) {
        const newNode = {
            key: newKey + 1,
            name: `node${newKey + 1}`,
            color: nodetype == 'Service' ? 'lightsalmon' : nodetype == 'End' ? 'lightblue' : null,
            properties: [
                { propName: "Type", propValue: nodetype, nodeType: true },
                { propName: "No of Memories", propValue: 500, numericValueOnly: true }
            ],
            memory: [
                { propName: "Memory Frequency (Hz)", propValue: 8e7, numericValueOnly: true },
                { propName: "Memory Expiry (s)", propValue: 100, numericValueOnly: true },
                { propName: "Memory Efficiency", propValue: 1, decimalValueAlso: true },
                { propName: "Memory Fidelity", propValue: 0.93, decimalValueAlso: true }
            ], isVisible: false
        };

        return newNode
    }
    addNewLink(linkKey, adornedPart, newNode) {
        return {
            key: linkKey + 1,
            from: adornedPart.data.key,
            to: newNode.key,
            distance: 70,
            attenuation: 0.0001
        };
    }
    getQuantumConnections(diagramModel, powerLoss) {
        var linkarray: any[]
        let links = []
        for (var i = 0; i < diagramModel.linkDataArray.length; i++) {
            linkarray = []
            var from = diagramModel.findNodeDataForKey(diagramModel.linkDataArray[i].from).name
            var to = diagramModel.findNodeDataForKey(diagramModel.linkDataArray[i].to).name
            linkarray.push(from);
            linkarray.push(to);
            let linkData = {
                Nodes: linkarray,
                Attenuation: diagramModel.linkDataArray[i].attenuation,
                Distance: diagramModel.linkDataArray[i].distance,
                powerLoss: powerLoss
            }
            links.push(linkData)
        }
        return links
    }

    getNodeElement() {

    }
    addSwapSuccessInMemory(newNode, diagramModel) {
        console.log("NodeDataArray-before", diagramModel.model.nodeDataArray)
        let node = diagramModel.model.nodeDataArray.find(node => node.key == newNode.key);
        node.memory.push({ propName: "Swap Success Probability", propValue: 0.99, decimalValueAlso: true })

        // diagramModel.set(node)
        return node
    }
    removeSwapSuccessInMemory(newNode, diagramModel) {
        console.log("NodeDataArray", diagramModel.model.nodeDataArray)
        let node = diagramModel.model.nodeDataArray.find(node => node.key == newNode.key);
        node.memory.pop()
        console.log("NodeDataArray", diagramModel.model.nodeDataArray)
        // diagramModel.set(node)
        return node
    }
    buildPath(parents, targetNode) {
        const path = [];
        let currentNode = targetNode;
        while (currentNode) {
            path.unshift(currentNode);
            currentNode = parents.get(currentNode);
        }
        return path;
    }
    findRouteBFS(startNode, targetNode, myDiagram) {
        const queue = [];
        const visited = new Set();
        const routes = new Map();

        // Enqueue the start node
        queue.push([{ from: null, to: startNode.key }]);
        visited.add(startNode.key);

        while (queue.length > 0) {
            const currentRoute = queue.shift();
            const currentLink = currentRoute[currentRoute.length - 1];
            const currentNodeKey = currentLink.to;

            // Check if the current node is the target node
            if (currentNodeKey === targetNode.key) {
                return currentRoute;
            }

            // Iterate over the links of the current node
            const links = myDiagram.model.linkDataArray.filter(link => link.from === currentNodeKey);
            for (const link of links) {
                const connectedNodeKey = link.to;

                // Check if the connected node has not been visited
                if (!visited.has(connectedNodeKey)) {
                    const newRoute = [...currentRoute, link];
                    queue.push(newRoute);
                    visited.add(connectedNodeKey);
                    routes.set(connectedNodeKey, newRoute);
                }
            }
        }

        // If the target node was not found, return null
        return null;
    }
    isDirectLinkExists(fromNodekey, toNodekey, myDiagram) {
        console.log("LinkDataArray", myDiagram.model.linkDataArray)
        const node1 = this.findNodeWithKey(fromNodekey, myDiagram);
        console.log("node1", node1)
        const node2 = this.findNodeWithKey(toNodekey, myDiagram);
        console.log("node2", node2)
        const newLinkArray = myDiagram.model.linkDataArray.filter(link => (link.from === node1.key && link.to === node2.key) || (link.from === node2.key && link.to === node1.key));
        console.log("newLinkArray", newLinkArray)
        if (newLinkArray.length == 0) {
            return true;
        }
        return false;
    }
    findNodeWithKey(key, myDiagram) {
        return myDiagram.model.nodeDataArray.find(node => node.key == key);
    }

}
