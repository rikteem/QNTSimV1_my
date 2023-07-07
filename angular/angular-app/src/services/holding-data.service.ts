import { Injectable } from '@angular/core';
@Injectable({
  providedIn: 'root'
})
export class HoldingDataService {
  routeFrom: string;
  homepageData = [{
    appId: 1, appName: 'E91 QKD', image: 'assets/images/apps/e91.png', content: 'Entanglement-based Quantum Key Distribution'
  },
  {
    appId: 2, appName: 'End-to-End EPR Pairs', image: 'assets/images/apps/e2e.png', content: 'End-to-End two party entanglement generation'
  }, {
    appId: 3, appName: 'Quantum Teleportation', image: 'assets/images/apps/tel.png', content: 'Quantum Teleportation from one node to another'
  }, {
    appId: 4, appName: 'End-to-end GHZ', image: 'assets/images/apps/ghz.png', content: 'End-to-End three party entanglement generation'
  }, {
    appId: 5, appName: 'Seminal QSDC', image: 'assets/images/apps/seminalqsdc.png', content: 'A high capacity QKD scheme with EPR pairs'
  }, {
    appId: 6, appName: 'Ping-Pong QSDC', image: 'assets/images/apps/pingpong.png', content: 'A deterministic secure direct communication scheme using EPR pairs'
  }, {
    appId: 7, appName: 'QSDC with user authentication', image: 'assets/images/apps/qsdcauth.png', content: 'An arbitrary basis QSDC scheme with mutual user authentication'
  }, {
    appId: 8, appName: 'Quantum Dialogue', image: 'assets/images/apps/spqd.png', content: 'A node-to-node quantum dialogue protocol using batches of single photons'
  }, {
    appId: 9, appName: 'QSDC with Teleportation', image: 'assets/images/apps/qsdctel.png', content: 'A teleportation scheme for QSDC'
  }, {
    appId: 10, appName: 'MDI-QSDC with user authentication', image: 'assets/images/apps/mdiauth.png', content: 'AN MDI-QSDC scheme with mutual user authentication and message integrity check'
  },]
  appData = {
    1: 'E91 QKD',
    2: 'End-to-End EPR Pairs',
    3: 'Quantum Teleportation',
    4: 'End-to-end GHZ',
    5: 'Seminal QSDC',
    6: 'Ping-Pong QSDC',
    7: 'QSDC with user authentication',
    8: 'Quantum Dialogue',
    9: 'QSDC with Teleportation',
    10: 'MDI-QSDC with user authentication',
  }
  spqd = {}
  getRoute() {
    return this.routeFrom
  }
  setRoute(route: string) {
    this.routeFrom = route
  }
  qsdct: any
  appDescription: any = [
    {
      title: 'Entanglement Generation', description: 'Entanglement is crucial for Quantum Communications and Computing applications. It can be created between two parties using SPDC or between multiple parties using GHZ and other multi- party states.Entanglement is essential for Quantum Teleportation, allowing quantum state transfer regardless of distance.'
    },
    {
      title: 'End-to-End Entanglement Distribution', description: 'Entanglement distribution is a crucial part of Quantum Networks, but it faces challenges due to distance constraints,entanglement fidelity, and quantum data decoherence.However, Entanglement Swapping and Purification offer interesting solutions.Entanglement Swapping involves using pre- shared entanglement between two nodes to establish distant entanglement by swapping immediate neighbors.Purification uses many entangled qubits to create fresh entanglement of higher quality than existing qubits, enabling remote parties to share entanglement.'
    },
    {
      title: 'Quantum Error Correction', description: 'The implementation of quantum error correction can significantly enhance the effectiveness and reliability of quantum networks in real-world applications. By detecting and correcting errors that arise during the transmission of quantum information, quantum error correction techniques such as error-correcting codes and quantum repeaters can enable secure communication and distributed quantum computing. As research in this area continues, improvements in quantum error correction protocols are expected, leading to more reliable and robust quantum networks that can power a range of practical applications.'
    },
    {
      title: 'Quantum Teleportation', description: 'Quantum teleportation transfers the state of a quantum particle across great distances using entanglement, without any physical transfer of the particle.With perfect security, it has the potential to revolutionize information exchange, from secure communications to data transfer.It represents a significant development in quantum mechanics with implications for the future of communication.'
    },
    {
      title: 'Quantum Key Distribution', description: 'BB84 Quantum Key Distribution, proposed by Bennett and Brassard in 1984, is the first quantum cryptographic protocol. It allows remote users to establish a shared secret key based on quantum physics, ensuring security. The key is used to encrypt the message, which is then transmitted through a classical channel. Two transmissions are required in a QKD-based communication.'
    },
    {
      title: 'Quantum Secure Direct Communication', description: "Unlike classical cryptography, some quantum protocols like Quantum Secure Direct Communication (QSDC) don't require any explicit keys for secure message transmission.QSDC allows direct transmission of a secret message from sender to receiver without any classical communication of ciphertext.It combines QKD and classical communication into one quantum communication, and has the potential to revolutionize secure communications and networking."
    },
    {
      title: 'Quantum Secret Sharing', description: "Compared to classical cryptography, quantum cryptography offers stronger security based on the laws of quantum mechanics. Quantum secret sharing, which utilizes quantum entanglement, offers a higher level of security for distributing secret messages among multiple parties than classical methods. With the growing need for secure communication, quantum cryptography and secret sharing are becoming crucial tools for safeguarding sensitive information."
    },
    {
      title: 'Distributed Quantum Computing', description: "Distributed quantum computing is a promising new approach that uses a network of interconnected quantum processors instead of a single large quantum computer. This approach offers advantages such as increased fault tolerance, scalability, and performance, enabling new applications and problem-solving capabilities. Though still in early stages, distributed quantum computing has already shown promising results and has the potential to transform the field in the future. With continued research, we can expect significant advancements and new use cases in quantum computing."
    },
  ]

  getClassicalConnections(nodes: any) {
    var tempcc = []
    var cc = []
    if (nodes.length != 0) {

      let ccreq;
      var distance
      var delay
      for (var i = 0; i < nodes.length; i++) {
        for (var j = 0; j < nodes.length; j++) {
          tempcc.push([nodes[i].Name, nodes[j].Name]);
        }
      }
      if (tempcc.length != 0) {
        for (var i = 0; i < tempcc.length; i++) {
          if (tempcc[i][0] == tempcc[i][1]) {
            distance = 0;
            delay = 0;
          } else {
            distance = 1000;
            delay = 10000000000;
          }
          ccreq = {
            Nodes: tempcc[i],
            Delay: delay,
            Distance: distance
          }
          cc.push(ccreq)
        }
      }

    }
    return cc
  }
  getAppDescription() {
    return this.appDescription
  }
  constructor() { }
  getQSDCT() {
    return this.qsdct;
  }
  getSpqd() {
    return this.spqd;
  }
  getHomePageData() {
    return this.homepageData
  }
  getAppData() {
    return this.appData
  }
}

